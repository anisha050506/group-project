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
    feedback         "was the match good?" -> training data for the ML model

STATUS:   Step 3 – tables + connection work. Functions marked TODO must be coded.
          get_user_by_id() is a finished EXAMPLE: copy its pattern.
AI NOTE:  Generated with Claude (Anthropic), 15.11.2026 – see docs/ai_usage.md
===============================================================================
"""

import os
import sqlite3

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
"""


# =============================================================================
# Connection & setup   (DONE)
# =============================================================================
def get_connection() -> sqlite3.Connection:
    """Open the database. Rows behave like dicts: row["name"]."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create all tables if they don't exist. Safe to call on every app run."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def reset_db() -> None:
    """Delete the database file and recreate empty tables (used by seed_data.py)."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()


# =============================================================================
# Users   (get_user_by_id = finished example, rest TODO)
# =============================================================================
def get_user_by_id(user_id: int) -> dict | None:
    """EXAMPLE: return one user as a dict, or None if not found."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def get_user_by_email(email: str) -> dict | None:
    """TODO: same as get_user_by_id, but search by email (used for login)."""
    raise NotImplementedError("TODO (Person B): get_user_by_email")


def create_user(email: str, password_hash: str, role: str, name: str) -> int:
    """TODO: INSERT a new user and return the new user_id (cursor.lastrowid)."""
    raise NotImplementedError("TODO (Person B): create_user")


def update_profile(user_id: int, data: dict) -> None:
    """
    TODO: UPDATE the users row with the values in `data`.
    `data` keys = column names, e.g. {"name": "Ana", "tidiness": 7, ...}
    Tip: build "SET name = ?, tidiness = ?" from data.keys() – but only allow
    known column names (never put user text directly into SQL!).
    """
    raise NotImplementedError("TODO (Person B): update_profile")


def update_role(user_id: int, role: str) -> None:
    """TODO: change role ('search_wg' <-> 'offer_wg'), used by the role switch."""
    raise NotImplementedError("TODO (Person B): update_role")


def get_all_seekers() -> list[dict]:
    """TODO: all users with role 'search_wg' (+ their search_criteria, via JOIN)."""
    raise NotImplementedError("TODO (Person B): get_all_seekers")


# =============================================================================
# Search criteria (seekers)   TODO
# =============================================================================
def save_search_criteria(user_id: int, data: dict) -> None:
    """TODO: INSERT OR REPLACE the row in search_criteria for this user."""
    raise NotImplementedError("TODO (Person B): save_search_criteria")


def get_search_criteria(user_id: int) -> dict | None:
    """TODO: return the seeker's criteria as a dict, or None."""
    raise NotImplementedError("TODO (Person B): get_search_criteria")


# =============================================================================
# WGs   TODO
# =============================================================================
def create_wg(data: dict, owner_user_id: int) -> int:
    """
    TODO: INSERT a WG, then add the owner to wg_members with is_main_tenant=1.
    Return the new wg_id.
    """
    raise NotImplementedError("TODO (Person B): create_wg")


def update_wg(wg_id: int, data: dict) -> None:
    """TODO: UPDATE the WG row (same idea as update_profile)."""
    raise NotImplementedError("TODO (Person B): update_wg")


def get_wg(wg_id: int) -> dict | None:
    """TODO: return one WG as a dict."""
    raise NotImplementedError("TODO (Person B): get_wg")


def get_wg_for_user(user_id: int) -> dict | None:
    """TODO: the WG this user lives in (via wg_members), or None."""
    raise NotImplementedError("TODO (Person B): get_wg_for_user")


def get_all_active_wgs() -> list[dict]:
    """TODO: all WGs with is_active = 1 AND is_verified = 1."""
    raise NotImplementedError("TODO (Person B): get_all_active_wgs")


def add_wg_member(wg_id: int, user_id: int, is_main_tenant: bool = False) -> None:
    """TODO: INSERT into wg_members."""
    raise NotImplementedError("TODO (Person B): add_wg_member")


def get_wg_members(wg_id: int) -> list[dict]:
    """TODO: all users living in this WG (JOIN wg_members + users)."""
    raise NotImplementedError("TODO (Person B): get_wg_members")


def get_wg_lifestyle_profile(wg_id: int) -> dict:
    """
    TODO: average slider values of all WG members -> {"tidiness": 6.5, ...}
    This is how a WG gets a "personality" to compare with seekers.
    Tip: SELECT AVG(tidiness) AS tidiness, AVG(...) ... FROM users JOIN wg_members ...
    """
    raise NotImplementedError("TODO (Person B): get_wg_lifestyle_profile")


# =============================================================================
# Swipes & matches   TODO
# =============================================================================
def save_swipe(seeker_id: int, wg_id: int, swiped_by: str, liked: bool) -> bool:
    """
    TODO: save a like/pass. swiped_by = 'seeker' or 'wg'.
    After saving a LIKE, check if the other side also liked
    -> if yes, INSERT into matches and return True ("It's a match!").
    Otherwise return False.
    """
    raise NotImplementedError("TODO (Person B): save_swipe")


def get_swiped_wg_ids(seeker_id: int) -> list[int]:
    """TODO: WG ids this seeker already swiped (so we don't show them again)."""
    raise NotImplementedError("TODO (Person B): get_swiped_wg_ids")


def get_seekers_who_liked_wg(wg_id: int) -> list[dict]:
    """TODO: seekers who liked this WG and the WG hasn't answered yet."""
    raise NotImplementedError("TODO (Person B): get_seekers_who_liked_wg")


def get_matches_for_user(user_id: int) -> list[dict]:
    """TODO: all matches where the user is the seeker OR a member of the WG."""
    raise NotImplementedError("TODO (Person B): get_matches_for_user")


def update_match(match_id: int, data: dict) -> None:
    """TODO: e.g. {"viewing_done": 1} or {"status": "offered"}."""
    raise NotImplementedError("TODO (Person B): update_match")


# =============================================================================
# Messages & feedback   TODO
# =============================================================================
def send_message(match_id: int, sender_id: int, text: str) -> None:
    """TODO: INSERT a chat message."""
    raise NotImplementedError("TODO (Person B): send_message")


def get_messages(match_id: int) -> list[dict]:
    """TODO: all messages of a match, oldest first."""
    raise NotImplementedError("TODO (Person B): get_messages")


def save_feedback(seeker_id: int, wg_id: int, satisfied: bool, comment: str = "") -> None:
    """TODO: INSERT into feedback (asked ~3 months after moving in)."""
    raise NotImplementedError("TODO (Person B): save_feedback")


def get_training_data():
    """
    TODO: return a pandas DataFrame for the ML model: one row per feedback,
    with the seeker's sliders, the WG's average sliders and `satisfied`.
    Tip: pandas.read_sql_query(sql, conn)
    """
    raise NotImplementedError("TODO (Person B + D): get_training_data")
