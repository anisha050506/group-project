"""
===============================================================================
FILE:     core/database.py
OWNER:    Person B – Data
-------------------------------------------------------------------------------
PURPOSE
    Everything that talks to the SQLite database (data/wg_match.db).
    Pages NEVER write SQL themselves – they call a function from this file,
    e.g.  database.get_user_by_id(5)  or  database.save_swipe(...).

WHAT BELONGS HERE
    - creating the tables (init_db)
    - one small function per read/write action ("CRUD": create, read,
      update, delete), returning plain Python dicts / lists of dicts
WHAT DOES NOT BELONG HERE
    - Streamlit code, match-score maths (-> matching.py), password hashing
      (-> auth.py)

TABLES (details: docs/database_schema.md)
    users            account + profile + 8 behavioural sliders
    search_criteria  extra info for seekers (max rent, move-in date, ...)
    wgs              the flat / free room
    wg_members       which users live in which WG (main tenant yes/no)
    swipes           every like / pass (seeker -> WG and WG -> seeker)
    matches          created when BOTH sides liked each other
    messages         chat messages inside a match
    conversation_reads  saved read position for each chat participant
    feedback         "was the match good?" -> training data for the ML model

STATUS:   Tables and read/write functions implemented.
AI NOTE:  Generated with Claude (Anthropic), 15.11.2026 – see docs/ai_usage.md
          Database functions completed with OpenAI Codex, 19.11.2026.
===============================================================================
"""

import os
import sqlite3
from contextlib import closing

import pandas as pd

from core.config import DB_PATH, SLIDER_KEYS

# The 8 slider columns are generated from config.py so they always match.
_SLIDER_COLUMNS = ",\n    ".join(f"{key} INTEGER" for key in SLIDER_KEYS)

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS users (
    user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    email          TEXT UNIQUE NOT NULL,
    password_hash  TEXT NOT NULL,                 -- never the plain password!
    role           TEXT CHECK (role IN ('search_wg', 'offer_wg')),
    name           TEXT,
    birth_year     INTEGER,                       -- year, not age (never outdated)
    gender         TEXT,
    languages      TEXT,                          -- comma separated, e.g. "DE,EN"
    degree         TEXT,
    study_level    TEXT,
    bio            TEXT,
    photo_path     TEXT,
    is_verified    INTEGER DEFAULT 0,             -- 1 = verified HSG student
    {_SLIDER_COLUMNS},
    created_at     TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS search_criteria (
    user_id                   INTEGER PRIMARY KEY REFERENCES users(user_id),
    max_rent                  REAL,
    move_in_date              TEXT,               -- ISO date "2027-02-01"
    max_travel_time           INTEGER,            -- minutes to HSG
    preferred_flatmate_gender TEXT,
    smoker                    INTEGER             -- 0 / 1
);

CREATE TABLE IF NOT EXISTS wgs (
    wg_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    title             TEXT,
    address           TEXT,
    district          TEXT,
    postcode          TEXT,
    latitude          REAL,
    longitude         REAL,
    rent_chf          REAL,                       -- per month incl. utilities
    utilities_chf     REAL,
    deposit_chf       REAL,
    room_size_m2      REAL,
    flat_size_m2      REAL,
    num_rooms         REAL,
    num_flatmates     INTEGER,
    furnished         INTEGER,
    private_bathroom  INTEGER,
    balcony           INTEGER,
    amenities         TEXT,                       -- comma separated
    available_from    TEXT,
    available_until   TEXT,                       -- NULL = unlimited
    min_rental_months INTEGER,
    wg_type           TEXT,
    smoking_allowed   TEXT,
    pets_allowed      INTEGER,
    preferred_gender  TEXT,                       -- any / women only / men only
    travel_time_min   INTEGER,                    -- cached result of transport API
    description       TEXT,
    photo_path        TEXT,
    is_verified       INTEGER DEFAULT 0,          -- address verified (mock)
    is_active         INTEGER DEFAULT 1,          -- 0 = room taken / hidden
    created_at        TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wg_members (
    wg_id          INTEGER REFERENCES wgs(wg_id),
    user_id        INTEGER REFERENCES users(user_id),
    is_main_tenant INTEGER DEFAULT 0,
    PRIMARY KEY (wg_id, user_id)
);

CREATE TABLE IF NOT EXISTS swipes (
    swipe_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    seeker_id  INTEGER REFERENCES users(user_id),
    wg_id      INTEGER REFERENCES wgs(wg_id),
    swiped_by  TEXT CHECK (swiped_by IN ('seeker', 'wg')),
    liked      INTEGER,                           -- 1 = like, 0 = pass
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (seeker_id, wg_id, swiped_by)
);

CREATE TABLE IF NOT EXISTS matches (
    match_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    seeker_id    INTEGER REFERENCES users(user_id),
    wg_id        INTEGER REFERENCES wgs(wg_id),
    status       TEXT DEFAULT 'open',             -- open / offered / accepted / declined
    viewing_done INTEGER DEFAULT 0,
    created_at   TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (seeker_id, wg_id)
);

CREATE TABLE IF NOT EXISTS messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id   INTEGER REFERENCES matches(match_id),
    sender_id  INTEGER REFERENCES users(user_id),
    text       TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    seeker_id   INTEGER REFERENCES users(user_id),
    wg_id       INTEGER REFERENCES wgs(wg_id),
    satisfied   INTEGER,                          -- 1 = good match, 0 = not
    comment     TEXT,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

-- AI-generated: OpenAI Codex, 19.11.2026. Persist each participant's chat read position.
CREATE TABLE IF NOT EXISTS conversation_reads (
    match_id             INTEGER REFERENCES matches(match_id),
    user_id              INTEGER REFERENCES users(user_id),
    last_read_message_id INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (match_id, user_id)
);
CREATE INDEX IF NOT EXISTS messages_match_order ON messages(match_id, message_id);
"""


# =============================================================================
# Connection & setup   (DONE)
# =============================================================================
def get_connection() -> sqlite3.Connection:
    """Open the database. Rows behave like dicts: row["name"]."""
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create all tables if they don't exist. Safe to call on every app run."""
    with closing(get_connection()) as conn, conn:
        conn.executescript(SCHEMA)


def reset_db() -> None:
    """Delete the database file and recreate empty tables (used by seed_data.py)."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()


# =============================================================================
# Users
# =============================================================================
def get_user_by_id(user_id: int) -> dict | None:
    """Return one user as a dict, or None if not found."""
    with closing(get_connection()) as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def get_user_by_email(email: str) -> dict | None:
    """Find an account by its normalized email address."""
    with closing(get_connection()) as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    return dict(row) if row else None


def create_user(email: str, password_hash: str, role: str, name: str) -> int:
    """Insert an account and return its new user_id."""
    with closing(get_connection()) as conn, conn:
        cursor = conn.execute(
            "INSERT INTO users (email, password_hash, role, name) VALUES (?, ?, ?, ?)",
            (email.strip().lower(), password_hash, role, name),
        )
        return cursor.lastrowid


# AI-generated: OpenAI Codex, 19.11.2026. Prompt: implement the SQLite database
# for all project forms, following the supplied sqlite3 / pandas example.
_PROFILE_FIELDS = {
    "name", "birth_year", "gender", "languages", "degree", "study_level", "bio",
    "photo_path", "is_verified", *SLIDER_KEYS,
}
_CRITERIA_FIELDS = {
    "max_rent", "move_in_date", "max_travel_time", "preferred_flatmate_gender", "smoker",
}
_WG_FIELDS = {
    "title", "address", "district", "postcode", "latitude", "longitude", "rent_chf",
    "utilities_chf", "deposit_chf", "room_size_m2", "flat_size_m2", "num_rooms",
    "num_flatmates", "furnished", "private_bathroom", "balcony", "amenities",
    "available_from", "available_until", "min_rental_months", "wg_type",
    "smoking_allowed", "pets_allowed", "preferred_gender", "travel_time_min",
    "description", "photo_path", "is_verified", "is_active",
}


def _validate_fields(data: dict, allowed: set[str]) -> None:
    """Only allow known column names in dynamically built SQL."""
    unknown = set(data) - allowed
    if unknown:
        raise ValueError(f"Unknown database fields: {', '.join(sorted(unknown))}")


def _update_row(table: str, id_column: str, row_id: int, data: dict, allowed: set[str]) -> None:
    """Update allowed fields. Table and id column are internal constants."""
    _validate_fields(data, allowed)
    if not data:
        return
    assignments = ", ".join(f"{column} = ?" for column in data)
    with closing(get_connection()) as conn, conn:
        conn.execute(
            f"UPDATE {table} SET {assignments} WHERE {id_column} = ?",
            [*data.values(), row_id],
        )


def update_profile(user_id: int, data: dict) -> None:
    """Save profile fields and lifestyle sliders; None is stored as SQL NULL."""
    _update_row("users", "user_id", user_id, data, _PROFILE_FIELDS)


def update_role(user_id: int, role: str) -> None:
    """Switch between seeker and WG provider."""
    _update_row("users", "user_id", user_id, {"role": role}, {"role"})


def get_all_seekers() -> list[dict]:
    """Return seekers, including those who have not entered criteria yet."""
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT u.*, c.max_rent, c.move_in_date, c.max_travel_time, "
            "c.preferred_flatmate_gender, c.smoker "
            "FROM users u LEFT JOIN search_criteria c ON c.user_id = u.user_id "
            "WHERE u.role = 'search_wg' ORDER BY u.user_id"
        ).fetchall()
    return [dict(row) for row in rows]


# =============================================================================
# Search criteria (seekers)
# =============================================================================
def save_search_criteria(user_id: int, data: dict) -> None:
    """Insert criteria or update supplied fields without clearing other fields."""
    _validate_fields(data, _CRITERIA_FIELDS)
    columns = ["user_id", *data]
    placeholders = ", ".join("?" for _ in columns)
    assignments = ", ".join(f"{column} = excluded.{column}" for column in data)
    conflict = f"DO UPDATE SET {assignments}" if data else "DO NOTHING"
    with closing(get_connection()) as conn, conn:
        conn.execute(
            f"INSERT INTO search_criteria ({', '.join(columns)}) VALUES ({placeholders}) "
            f"ON CONFLICT(user_id) {conflict}",
            [user_id, *data.values()],
        )


def get_search_criteria(user_id: int) -> dict | None:
    """Return the seeker's criteria, or None."""
    with closing(get_connection()) as conn:
        row = conn.execute("SELECT * FROM search_criteria WHERE user_id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


# =============================================================================
# WGs
# =============================================================================
def create_wg(data: dict, owner_user_id: int) -> int:
    """Create a WG and its main tenant in one transaction; return the wg_id."""
    _validate_fields(data, _WG_FIELDS)
    with closing(get_connection()) as conn, conn:
        if data:
            columns = ", ".join(data)
            placeholders = ", ".join("?" for _ in data)
            cursor = conn.execute(
                f"INSERT INTO wgs ({columns}) VALUES ({placeholders})", list(data.values())
            )
        else:
            cursor = conn.execute("INSERT INTO wgs DEFAULT VALUES")
        wg_id = cursor.lastrowid
        conn.execute(
            "INSERT INTO wg_members (wg_id, user_id, is_main_tenant) VALUES (?, ?, 1)",
            (wg_id, owner_user_id),
        )
    return wg_id


def update_wg(wg_id: int, data: dict) -> None:
    """Save supplied WG listing fields."""
    _update_row("wgs", "wg_id", wg_id, data, _WG_FIELDS)


def get_wg(wg_id: int) -> dict | None:
    """Return one WG, or None."""
    with closing(get_connection()) as conn:
        row = conn.execute("SELECT * FROM wgs WHERE wg_id = ?", (wg_id,)).fetchone()
    return dict(row) if row else None


def get_wg_for_user(user_id: int) -> dict | None:
    """Return a user's WG, preferring one where they are the main tenant."""
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT w.* FROM wgs w JOIN wg_members m ON m.wg_id = w.wg_id "
            "WHERE m.user_id = ? ORDER BY m.is_main_tenant DESC, w.wg_id LIMIT 1",
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def get_all_active_wgs() -> list[dict]:
    """Return active, verified listings."""
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT * FROM wgs WHERE is_active = 1 AND is_verified = 1 ORDER BY wg_id"
        ).fetchall()
    return [dict(row) for row in rows]


def add_wg_member(wg_id: int, user_id: int, is_main_tenant: bool = False) -> None:
    """Add a member, or update their main-tenant flag if already present."""
    with closing(get_connection()) as conn, conn:
        conn.execute(
            "INSERT INTO wg_members (wg_id, user_id, is_main_tenant) VALUES (?, ?, ?) "
            "ON CONFLICT(wg_id, user_id) DO UPDATE SET is_main_tenant = excluded.is_main_tenant",
            (wg_id, user_id, int(is_main_tenant)),
        )


def get_wg_members(wg_id: int) -> list[dict]:
    """Return members and their main-tenant flags."""
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT u.*, m.is_main_tenant FROM users u "
            "JOIN wg_members m ON m.user_id = u.user_id WHERE m.wg_id = ? "
            "ORDER BY m.is_main_tenant DESC, u.user_id", (wg_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_wg_lifestyle_profile(wg_id: int) -> dict:
    """Average each slider, ignoring NULLs; an unfilled slider stays None."""
    averages = ", ".join(f"AVG(u.{key}) AS {key}" for key in SLIDER_KEYS)
    with closing(get_connection()) as conn:
        row = conn.execute(
            f"SELECT {averages} FROM users u JOIN wg_members m ON m.user_id = u.user_id "
            "WHERE m.wg_id = ?", (wg_id,),
        ).fetchone()
    return dict(row)


# =============================================================================
# Swipes & matches
# =============================================================================
def save_swipe(seeker_id: int, wg_id: int, swiped_by: str, liked: bool) -> bool:
    """Save a like/pass and return True only when a new mutual match is made."""
    if swiped_by not in {"seeker", "wg"}:
        raise ValueError("swiped_by must be 'seeker' or 'wg'")
    with closing(get_connection()) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        available = conn.execute(
            "SELECT 1 FROM wgs WHERE wg_id = ? AND is_active = 1 AND is_verified = 1", (wg_id,),
        ).fetchone()
        if not available:
            raise ValueError("This listing is no longer active and verified.")
        if conn.execute("SELECT 1 FROM wg_members WHERE wg_id = ? AND user_id = ?", (wg_id, seeker_id)).fetchone():
            raise ValueError("You cannot swipe on your own WG.")
        if conn.execute("SELECT 1 FROM matches WHERE seeker_id = ? AND status = 'accepted'", (seeker_id,)).fetchone():
            raise ValueError("This seeker has already accepted a room.")
        conn.execute(
            "INSERT INTO swipes (seeker_id, wg_id, swiped_by, liked) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(seeker_id, wg_id, swiped_by) DO UPDATE SET "
            "liked = excluded.liked, created_at = CURRENT_TIMESTAMP",
            (seeker_id, wg_id, swiped_by, int(liked)),
        )
        other_side = "wg" if swiped_by == "seeker" else "seeker"
        reciprocal = conn.execute(
            "SELECT 1 FROM swipes WHERE seeker_id = ? AND wg_id = ? "
            "AND swiped_by = ? AND liked = 1", (seeker_id, wg_id, other_side),
        ).fetchone()
        if liked and reciprocal:
            cursor = conn.execute(
                "INSERT INTO matches (seeker_id, wg_id) VALUES (?, ?) "
                "ON CONFLICT(seeker_id, wg_id) DO NOTHING", (seeker_id, wg_id),
            )
            return cursor.rowcount == 1
    return False


def undo_last_swipe(seeker_id: int, wg_id: int, swiped_by: str) -> None:
    """Take back a just-made like/pass so a misclick is not permanent. If that
    like had created a match that is still open with no messages yet, remove the
    match too, so the candidate reappears in the ranking."""
    with closing(get_connection()) as conn, conn:
        conn.execute(
            "DELETE FROM swipes WHERE seeker_id = ? AND wg_id = ? AND swiped_by = ?",
            (seeker_id, wg_id, swiped_by),
        )
        match = conn.execute(
            "SELECT match_id, status FROM matches WHERE seeker_id = ? AND wg_id = ?",
            (seeker_id, wg_id),
        ).fetchone()
        if match and match["status"] == "open" and not conn.execute(
            "SELECT 1 FROM messages WHERE match_id = ? LIMIT 1", (match["match_id"],)
        ).fetchone():
            conn.execute("DELETE FROM conversation_reads WHERE match_id = ?", (match["match_id"],))
            conn.execute("DELETE FROM matches WHERE match_id = ?", (match["match_id"],))


def get_swiped_wg_ids(seeker_id: int) -> list[int]:
    """Return only WGs swiped by the seeker, excluding provider-only swipes."""
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT wg_id FROM swipes WHERE seeker_id = ? AND swiped_by = 'seeker' "
            "ORDER BY wg_id", (seeker_id,),
        ).fetchall()
    return [row["wg_id"] for row in rows]


def get_seekers_who_liked_wg(wg_id: int) -> list[dict]:
    """Return seekers who liked the WG and have no provider response yet."""
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT u.* FROM users u JOIN swipes s ON s.seeker_id = u.user_id "
            "WHERE u.role = 'search_wg' AND s.wg_id = ? AND s.swiped_by = 'seeker' "
            "AND s.liked = 1 AND NOT EXISTS (SELECT 1 FROM swipes response "
            "WHERE response.seeker_id = s.seeker_id AND response.wg_id = s.wg_id "
            "AND response.swiped_by = 'wg') ORDER BY s.created_at, s.swipe_id", (wg_id,),
        ).fetchall()
    return [dict(row) for row in rows]


# AI-generated: OpenAI Codex, 19.11.2026. Prompt: fix provider swiping so either side can swipe first.
def get_swiped_seeker_ids(wg_id: int) -> list[int]:
    """Seekers this WG has already liked or passed, regardless of seeker votes."""
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT seeker_id FROM swipes WHERE wg_id = ? AND swiped_by = 'wg' "
            "ORDER BY seeker_id", (wg_id,),
        ).fetchall()
    return [row["seeker_id"] for row in rows]


def get_matches_for_user(user_id: int) -> list[dict]:
    """Return matches visible to the seeker or any member, with display names."""
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT m.*, u.name AS seeker_name, w.title AS wg_title FROM matches m "
            "JOIN users u ON u.user_id = m.seeker_id JOIN wgs w ON w.wg_id = m.wg_id "
            "WHERE m.seeker_id = ? OR EXISTS (SELECT 1 FROM wg_members member "
            "WHERE member.wg_id = m.wg_id AND member.user_id = ?) "
            "ORDER BY m.created_at DESC, m.match_id DESC", (user_id, user_id),
        ).fetchall()
    return [dict(row) for row in rows]


def update_match(match_id: int, data: dict) -> None:
    """Update viewing completion or the offer status."""
    if "status" in data and data["status"] not in {"open", "offered", "accepted", "declined"}:
        raise ValueError("Unknown match status")
    _update_row("matches", "match_id", match_id, data, {"viewing_done", "status"})


# =============================================================================
# Messages & feedback
# =============================================================================
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: make conversations async and organize chats like WhatsApp.
def get_conversations_for_user(user_id: int) -> list[dict]:
    """Authorized inbox with latest-message previews and durable unread counts."""
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT m.*, u.name AS seeker_name, w.title AS wg_title, "
            "latest.message_id AS last_message_id, latest.text AS last_message_text, "
            "latest.created_at AS last_message_at, latest.sender_id AS last_sender_id, "
            "sender.name AS last_sender_name, COALESCE(r.last_read_message_id, 0) AS last_read_message_id, "
            "(SELECT COUNT(*) FROM messages unread WHERE unread.match_id = m.match_id "
            "AND unread.sender_id != ? AND unread.message_id > COALESCE(r.last_read_message_id, 0)) AS unread_count "
            "FROM matches m JOIN users u ON u.user_id = m.seeker_id "
            "JOIN wgs w ON w.wg_id = m.wg_id "
            "LEFT JOIN messages latest ON latest.message_id = "
            "(SELECT MAX(message_id) FROM messages WHERE match_id = m.match_id) "
            "LEFT JOIN users sender ON sender.user_id = latest.sender_id "
            "LEFT JOIN conversation_reads r ON r.match_id = m.match_id AND r.user_id = ? "
            "WHERE m.seeker_id = ? OR EXISTS (SELECT 1 FROM wg_members member "
            "WHERE member.wg_id = m.wg_id AND member.user_id = ?) "
            "ORDER BY COALESCE(latest.created_at, m.created_at) DESC, "
            "COALESCE(latest.message_id, 0) DESC, m.match_id DESC",
            (user_id, user_id, user_id, user_id),
        ).fetchall()
    return [dict(row) for row in rows]


def get_notification_counts(user_id: int) -> dict:
    """In-app notification badge data for a user: how many messages they have
    not read yet, and how many brand-new matches have no chat started. Both are
    derived live from existing tables, so no extra state is stored."""
    with closing(get_connection()) as conn:
        row = conn.execute(
            "WITH my_matches AS ("
            "  SELECT m.match_id FROM matches m WHERE m.seeker_id = ?"
            "  OR EXISTS (SELECT 1 FROM wg_members wm WHERE wm.wg_id = m.wg_id AND wm.user_id = ?)"
            ") "
            "SELECT "
            "(SELECT COUNT(*) FROM my_matches mm WHERE NOT EXISTS "
            "   (SELECT 1 FROM messages msg WHERE msg.match_id = mm.match_id)) AS new_matches, "
            "(SELECT COUNT(*) FROM messages msg JOIN my_matches mm ON mm.match_id = msg.match_id "
            "   LEFT JOIN conversation_reads r ON r.match_id = msg.match_id AND r.user_id = ? "
            "   WHERE msg.sender_id != ? "
            "   AND msg.message_id > COALESCE(r.last_read_message_id, 0)) AS unread_messages",
            (user_id, user_id, user_id, user_id),
        ).fetchone()
    new_matches = row["new_matches"] or 0
    unread_messages = row["unread_messages"] or 0
    return {
        "new_matches": new_matches,
        "unread_messages": unread_messages,
        "total": new_matches + unread_messages,
    }


def mark_conversation_read(match_id: int, user_id: int, last_message_id: int) -> None:
    """Advance only through displayed messages, without marking later arrivals read."""
    with closing(get_connection()) as conn, conn:
        cursor = conn.execute(
            "INSERT INTO conversation_reads (match_id, user_id, last_read_message_id) "
            "SELECT m.match_id, ?, COALESCE((SELECT MAX(message_id) FROM messages "
            "WHERE match_id = m.match_id AND message_id <= ?), 0) "
            "FROM matches m WHERE m.match_id = ? AND (m.seeker_id = ? OR EXISTS "
            "(SELECT 1 FROM wg_members member WHERE member.wg_id = m.wg_id AND member.user_id = ?)) "
            "ON CONFLICT(match_id, user_id) DO UPDATE SET last_read_message_id = "
            "MAX(conversation_reads.last_read_message_id, excluded.last_read_message_id)",
            (user_id, last_message_id, match_id, user_id, user_id),
        )
        if cursor.rowcount == 0:
            raise ValueError("Only a participant can read this conversation.")


def send_message(match_id: int, sender_id: int, text: str) -> None:
    """Insert a message from a seeker or member of the matched WG."""
    text = text.strip()
    if not text or len(text) > 4000:
        raise ValueError("Enter a message of 1–4000 characters.")
    with closing(get_connection()) as conn, conn:
        participant = conn.execute(
            "SELECT 1 FROM matches m WHERE m.match_id = ? AND (m.seeker_id = ? "
            "OR EXISTS (SELECT 1 FROM wg_members member "
            "WHERE member.wg_id = m.wg_id AND member.user_id = ?))",
            (match_id, sender_id, sender_id),
        ).fetchone()
        if not participant:
            raise ValueError("Sender must belong to this match")
        conn.execute(
            "INSERT INTO messages (match_id, sender_id, text) VALUES (?, ?, ?)",
            (match_id, sender_id, text),
        )


def get_messages(match_id: int) -> list[dict]:
    """Return a match's messages, oldest first, including sender names."""
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT m.*, u.name AS sender_name FROM messages m "
            "JOIN users u ON u.user_id = m.sender_id WHERE m.match_id = ? "
            "ORDER BY m.created_at, m.message_id", (match_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def save_feedback(seeker_id: int, wg_id: int, satisfied: bool, comment: str = "") -> None:
    """Record satisfaction feedback for model training."""
    with closing(get_connection()) as conn, conn:
        conn.execute(
            "INSERT INTO feedback (seeker_id, wg_id, satisfied, comment) VALUES (?, ?, ?, ?)",
            (seeker_id, wg_id, int(satisfied), comment),
        )


def get_training_data() -> pd.DataFrame:
    """One row per resolved match with seeker_<slider>, wg_<slider>, and matched.

    The label is the real outcome of a match: matched = 1 when both sides
    accepted (status 'accepted'), 0 when it was declined. Only resolved matches
    (accepted or declined) are included; open and offered matches are still
    undecided. WG values are current member averages; missing sliders stay NaN.
    """
    averages = ", ".join(f"AVG(u.{key}) AS {key}" for key in SLIDER_KEYS)
    features = ", ".join(
        f"seeker.{key} AS seeker_{key}, profile.{key} AS wg_{key}" for key in SLIDER_KEYS
    )
    sql = f"""
        WITH wg_profiles AS (
            SELECT member.wg_id, {averages}
            FROM wg_members member JOIN users u ON u.user_id = member.user_id
            GROUP BY member.wg_id
        )
        SELECT m.match_id, m.seeker_id, m.wg_id, {features},
               CASE WHEN m.status = 'accepted' THEN 1 ELSE 0 END AS matched
        FROM matches m
        JOIN users seeker ON seeker.user_id = m.seeker_id
        LEFT JOIN wg_profiles profile ON profile.wg_id = m.wg_id
        WHERE m.status IN ('accepted', 'declined')
        ORDER BY m.match_id
    """
    with closing(get_connection()) as conn:
        return pd.read_sql_query(sql, conn)


# AI-generated: OpenAI Codex, 19.11.2026. Complete the match and tenancy workflow.
def mark_viewing_done(match_id: int, actor_id: int) -> None:
    """Only a member of the matched WG can confirm a viewing."""
    with closing(get_connection()) as conn, conn:
        cursor = conn.execute(
            "UPDATE matches SET viewing_done = 1 WHERE match_id = ? AND status = 'open' "
            "AND EXISTS (SELECT 1 FROM wg_members member WHERE member.wg_id = matches.wg_id "
            "AND member.user_id = ?)", (match_id, actor_id),
        )
        if not cursor.rowcount:
            raise ValueError("Only a WG member can record a viewing for an open match.")


def change_match_status(match_id: int, actor_id: int, status: str) -> None:
    """Enforce offer permissions and reserve a room atomically on acceptance."""
    with closing(get_connection()) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        match = conn.execute("SELECT * FROM matches WHERE match_id = ?", (match_id,)).fetchone()
        if not match:
            raise ValueError("Match not found.")
        main_tenant = conn.execute(
            "SELECT 1 FROM wg_members WHERE wg_id = ? AND user_id = ? AND is_main_tenant = 1",
            (match["wg_id"], actor_id),
        ).fetchone()
        is_seeker = actor_id == match["seeker_id"]
        if status == "offered":
            if not main_tenant or match["status"] != "open" or not match["viewing_done"]:
                raise ValueError("The main tenant can offer the room after a viewing.")
            available = conn.execute("SELECT is_active FROM wgs WHERE wg_id = ?", (match["wg_id"],)).fetchone()
            if not available or not available["is_active"]:
                raise ValueError("This room is no longer available.")
        elif status == "accepted":
            if not is_seeker or match["status"] != "offered":
                raise ValueError("Only the seeker can accept an offered room.")
            already_housed = conn.execute(
                "SELECT 1 FROM matches WHERE seeker_id = ? AND status = 'accepted' AND match_id != ?",
                (actor_id, match_id),
            ).fetchone()
            if already_housed:
                raise ValueError("You have already accepted a room.")
            cursor = conn.execute("UPDATE wgs SET is_active = 0 WHERE wg_id = ? AND is_active = 1", (match["wg_id"],))
            if not cursor.rowcount:
                raise ValueError("This room has already been taken.")
            conn.execute(
                "UPDATE matches SET status = 'declined' WHERE match_id != ? AND status IN ('open', 'offered') "
                "AND (wg_id = ? OR seeker_id = ?)", (match_id, match["wg_id"], actor_id),
            )
        elif status == "declined":
            if not (is_seeker or main_tenant) or match["status"] not in {"open", "offered"}:
                raise ValueError("Only the seeker or main tenant can decline an open match or offer.")
        else:
            raise ValueError("Unknown match transition.")
        conn.execute("UPDATE matches SET status = ? WHERE match_id = ?", (status, match_id))


def save_match_feedback(match_id: int, actor_id: int, satisfied: bool, comment: str = "") -> None:
    """One feedback submission per accepted match, by its seeker."""
    with closing(get_connection()) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        match = conn.execute(
            "SELECT * FROM matches WHERE match_id = ? AND seeker_id = ? AND status = 'accepted'",
            (match_id, actor_id),
        ).fetchone()
        if not match:
            raise ValueError("Only the seeker in an accepted match can leave feedback.")
        exists = conn.execute(
            "SELECT 1 FROM feedback WHERE seeker_id = ? AND wg_id = ?", (actor_id, match["wg_id"]),
        ).fetchone()
        if exists:
            raise ValueError("Feedback has already been recorded for this match.")
        conn.execute(
            "INSERT INTO feedback (seeker_id, wg_id, satisfied, comment) VALUES (?, ?, ?, ?)",
            (actor_id, match["wg_id"], int(satisfied), comment.strip()),
        )


def has_match_feedback(seeker_id: int, wg_id: int) -> bool:
    with closing(get_connection()) as conn:
        return conn.execute(
            "SELECT 1 FROM feedback WHERE seeker_id = ? AND wg_id = ?", (seeker_id, wg_id),
        ).fetchone() is not None


def remove_wg_member(wg_id: int, user_id: int, actor_id: int) -> None:
    """The main tenant can remove another member, but cannot remove themselves."""
    with closing(get_connection()) as conn, conn:
        main_tenant = conn.execute(
            "SELECT 1 FROM wg_members WHERE wg_id = ? AND user_id = ? AND is_main_tenant = 1",
            (wg_id, actor_id),
        ).fetchone()
        if not main_tenant or user_id == actor_id:
            raise ValueError("Only the main tenant can remove another flatmate.")
        conn.execute("DELETE FROM wg_members WHERE wg_id = ? AND user_id = ? AND is_main_tenant = 0", (wg_id, user_id))
