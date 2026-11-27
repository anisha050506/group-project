"""
===============================================================================
FILE:     data/seed_data.py       (run from the repository root with:
                                    python -m data.seed_data)
-------------------------------------------------------------------------------
PURPOSE
    Fills the database with realistic FAKE data so that everybody can test
    their page, the ML model has training data, and the demo video works
    long before real users exist.

AI NOTE:  Generated with Claude (Anthropic), 15.11.2026 – see docs/ai_usage.md
===============================================================================
"""

import datetime
import random
from contextlib import closing

from core import auth, database
from core.config import (
    AMENITIES, DEGREES, DISTRICTS, GENDERS, LANGUAGES, SLIDER_KEYS, SLIDER_MAX,
    SLIDER_MIN, SMOKING_OPTIONS, STUDY_LEVELS, WG_TYPES,
)

RANDOM_SEED = 42
NUM_SEEKERS = 60
NUM_WGS = 25
DEMO_PASSWORD = "demo1234"

FIRST_NAMES = [
    "Lena", "Noah", "Mila", "Luca", "Emma", "Elias", "Sofia", "Leon", "Lara", "Julian",
    "Nina", "David", "Sara", "Tim", "Alina", "Jan", "Chiara", "Nico", "Lea", "Fabio",
    "Zoe", "Marco", "Anna", "Felix", "Giulia", "Ben", "Clara", "Samuel", "Elena", "Max",
]
LAST_NAMES = [
    "Meier", "Keller", "Brunner", "Rossi", "Weber", "Huber", "Schmid", "Fischer", "Bianchi",
    "Moser", "Frei", "Baumann", "Gerber", "Müller", "Steiner", "Dubois", "Martin", "Costa",
]

# Approximate location and public-transport time to HSG per district (fake but
# plausible). Districts that are added later in config.py get the defaults.
DISTRICT_INFO = {
    #  district      latitude, longitude, minutes to HSG
    "Zentrum":     (47.4239, 9.3748, 12),
    "Rotmonten":   (47.4335, 9.3800, 6),
    "Rosenberg":   (47.4290, 9.3700, 8),
    "St. Georgen": (47.4140, 9.3810, 18),
    "Riethüsli":   (47.4170, 9.3600, 16),
    "Lachen":      (47.4205, 9.3555, 17),
    "St. Fiden":   (47.4300, 9.3960, 14),
    "Neudorf":     (47.4375, 9.4060, 22),
    "Langgasse":   (47.4340, 9.3880, 10),
    "Heiligkreuz": (47.4320, 9.4010, 15),
    "Bruggen":     (47.4115, 9.3300, 25),
    "Winkeln":     (47.4050, 9.3050, 30),
}
DEFAULT_DISTRICT_INFO = (47.4245, 9.3767, 20)


# =============================================================================
# Helpers
# =============================================================================
def clamp(value: float) -> int:
    """Keep a slider value inside SLIDER_MIN ... SLIDER_MAX."""
    return int(max(SLIDER_MIN, min(SLIDER_MAX, round(value))))


def random_sliders(base: dict | None = None, spread: float = 2.0) -> dict:
    """Random slider values; if `base` is given, values are close to it."""
    if base is None:
        return {key: random.randint(SLIDER_MIN, SLIDER_MAX) for key in SLIDER_KEYS}
    return {key: clamp(random.gauss(base[key], spread)) for key in SLIDER_KEYS}


def insert(conn, table: str, row: dict) -> int:
    """INSERT one row (dict: column -> value) and return the new id."""
    columns = ", ".join(row)
    placeholders = ", ".join("?" for _ in row)
    cursor = conn.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", list(row.values()))
    return cursor.lastrowid


def make_user(conn, password_hash: str, role: str, email: str, name: str, sliders: dict, **extra) -> int:
    """Create one user with a random profile; `extra` overrides any field."""
    row = {
        "email": email,
        "password_hash": password_hash,
        "role": role,
        "name": name,
        "birth_year": random.randint(1998, 2006),
        "gender": random.choice(GENDERS[:3]),
        "languages": ",".join(random.sample(LANGUAGES[:4], k=random.randint(1, 3))),
        "degree": random.choice(DEGREES),
        "study_level": random.choice(STUDY_LEVELS),
        "bio": "",
        "is_verified": 1,
        **sliders,
    }
    row.update(extra)
    return insert(conn, "users", row)


def similarity(a: dict, b: dict) -> float:
    """0 (opposite) ... 1 (identical): simple version of the match score."""
    diffs = [abs(a[key] - b[key]) for key in SLIDER_KEYS]
    return 1 - (sum(diffs) / len(diffs)) / SLIDER_MAX


def wg_profile(conn, wg_id: int) -> dict:
    """Average slider values of all members of a WG."""
    averages = ", ".join(f"AVG(u.{key})" for key in SLIDER_KEYS)
    row = conn.execute(
        f"SELECT {averages} FROM users u JOIN wg_members m ON u.user_id = m.user_id WHERE m.wg_id = ?",
        (wg_id,),
    ).fetchone()
    return dict(zip(SLIDER_KEYS, row))


# =============================================================================
# Named test accounts (documented in test_accounts.txt)
# =============================================================================
# These 16 fictional accounts each have their OWN password (unlike the shared
# DEMO_PASSWORD users). They are recreated here so they really exist on every
# deploy and in every fresh local database, matching test_accounts.txt. No
# swipes/matches are pre-created for them (same as the doc).
NAMED_TEST_SEEKERS = [
    ("Lena Meier", "wgtest.lena.meier@student.unisg.ch", "r4yVo_R6NmghzpKN"),
    ("Noah Keller", "wgtest.noah.keller@student.unisg.ch", "tDKEdcCgAWSMsQOi"),
    ("Mila Brunner", "wgtest.mila.brunner@student.unisg.ch", "da5lCL2046g-83mP"),
    ("Luca Rossi", "wgtest.luca.rossi@student.unisg.ch", "RzKtDCS9n20XfoQz"),
    ("Emma Weber", "wgtest.emma.weber@student.unisg.ch", "L6PZA_om5JVqEeEo"),
    ("Elias Huber", "wgtest.elias.huber@student.unisg.ch", "jTtjsuNwcBj3UWBF"),
    ("Sofia Schmid", "wgtest.sofia.schmid@student.unisg.ch", "NZuojVbLTnaiU48q"),
    ("Leon Fischer", "wgtest.leon.fischer@student.unisg.ch", "IKH13FYcddgaa9NI"),
]
NAMED_TEST_WGS = [
    {"title": "Rotmonten Kitchen WG", "district": "Rotmonten", "rent": 720,
     "main": ("Nina Baumann", "wgtest.nina.baumann@student.unisg.ch", "Pshq7885I-QK8sQu"),
     "flatmate": ("Alina Steiner", "wgtest.alina.steiner@student.unisg.ch", "0Rc2L3dgb0gXp3zs")},
    {"title": "Quiet Rosenberg WG", "district": "Rosenberg", "rent": 850,
     "main": ("David Frei", "wgtest.david.frei@student.unisg.ch", "O4OHFYzT83DNSKYe"),
     "flatmate": ("Jan Dubois", "wgtest.jan.dubois@student.unisg.ch", "MvJYRqj2BNBPRQoT")},
    {"title": "City Study WG", "district": "Zentrum", "rent": 950,
     "main": ("Sara Gerber", "wgtest.sara.gerber@student.unisg.ch", "vVTTNMCQreW5dBVa"),
     "flatmate": ("Chiara Bianchi", "wgtest.chiara.bianchi@student.unisg.ch", "wx17qtc2spclRcqh")},
    {"title": "Relaxed Langgasse WG", "district": "Langgasse", "rent": 680,
     "main": ("Tim Moser", "wgtest.tim.moser@student.unisg.ch", "B1wM56o1Y7BnNhIk"),
     "flatmate": ("Nico Costa", "wgtest.nico.costa@student.unisg.ch", "n_CsBeDmSM9MGvHu")},
]


def add_named_test_accounts(conn, today: datetime.date) -> None:
    """Create the 16 documented wgtest.* accounts, each with its own password,
    a complete profile, and (for providers) a verified WG with a flatmate."""
    for name, email, pw in NAMED_TEST_SEEKERS:
        user_id = make_user(conn, auth.hash_password(pw), "search_wg", email,
                            name.split()[0], random_sliders(), bio=f"{name} (test account).")
        insert(conn, "search_criteria", {
            "user_id": user_id,
            "max_rent": random.choice([700, 800, 900, 1000]),
            "move_in_date": (today + datetime.timedelta(days=random.randint(30, 120))).isoformat(),
            "max_travel_time": random.choice([15, 20, 25, 30]),
            "preferred_flatmate_gender": "any",
            "smoker": 0,
        })

    for wg in NAMED_TEST_WGS:
        lat, lon, minutes = DISTRICT_INFO.get(wg["district"], DEFAULT_DISTRICT_INFO)
        wg_id = insert(conn, "wgs", {
            "title": wg["title"], "address": f"{wg['district']}strasse {random.randint(1, 60)}",
            "district": wg["district"], "postcode": "9000", "latitude": lat, "longitude": lon,
            "rent_chf": wg["rent"], "utilities_chf": 80, "deposit_chf": wg["rent"] * 2,
            "room_size_m2": random.randint(12, 20), "flat_size_m2": random.randint(70, 110),
            "num_rooms": random.choice([3.5, 4, 4.5]), "num_flatmates": 2,
            "furnished": 1, "private_bathroom": 0, "balcony": 1,
            "amenities": "Washing machine,Wi-Fi,Dishwasher",
            "available_from": (today + datetime.timedelta(days=random.randint(14, 90))).isoformat(),
            "min_rental_months": 6, "wg_type": WG_TYPES[-1], "smoking_allowed": SMOKING_OPTIONS[0],
            "pets_allowed": 0, "preferred_gender": "any", "travel_time_min": minutes,
            "description": f"{wg['title']} - fictional demo listing.", "is_verified": 1,
        })
        vibe = random_sliders()
        for role_key, is_main in (("main", 1), ("flatmate", 0)):
            name, email, pw = wg[role_key]
            member_id = make_user(conn, auth.hash_password(pw), "offer_wg", email,
                                  name.split()[0], random_sliders(base=vibe, spread=1.5),
                                  bio=f"{name} (test account).")
            insert(conn, "wg_members", {"wg_id": wg_id, "user_id": member_id, "is_main_tenant": is_main})


def add_photo_wg(conn, today: datetime.date) -> None:
    """A single demo WG with a real photographed listing (a collage of the
    living room, kitchen and the room on offer). The image lives in assets/demo/
    and is referenced by a path relative to the project root, so it loads on any
    machine and on the deployed app."""
    lat, lon, minutes = DISTRICT_INFO.get("Zentrum", DEFAULT_DISTRICT_INFO)
    owner = make_user(
        conn, auth.hash_password(DEMO_PASSWORD), "offer_wg", "elena.fischer.demo@student.unisg.ch",
        "Elena", {"tidiness": 7, "sociability": 7, "noise_tolerance": 5, "guests": 5,
                  "sleep_rhythm": 5, "cooking_together": 8, "cleaning_schedule": 7, "time_at_home": 6},
        gender="female", birth_year=2001, languages="DE,EN", study_level="Master", degree="BWL",
        bio="Master's student. Our Altbau WG is bright and sociable; we cook together most weeks.",
    )
    wg_id = insert(conn, "wgs", {
        "title": "Sunny Altbau room in a central WG", "address": "Zentrumstrasse 14",
        "district": "Zentrum", "postcode": "9000", "latitude": lat, "longitude": lon,
        "rent_chf": 890, "utilities_chf": 90, "deposit_chf": 1780, "room_size_m2": 18,
        "flat_size_m2": 108, "num_rooms": 4.0, "num_flatmates": 2, "furnished": 1,
        "private_bathroom": 0, "balcony": 1, "amenities": "Washing machine,Wi-Fi,Dishwasher",
        "available_from": (today + datetime.timedelta(days=45)).isoformat(), "min_rental_months": 6,
        "wg_type": WG_TYPES[-1], "smoking_allowed": SMOKING_OPTIONS[0], "pets_allowed": 0,
        "preferred_gender": "any", "travel_time_min": minutes,
        "description": "Bright, high-ceilinged Altbau flat: a spacious living room, an open kitchen "
                       "with a dining table, and a cosy attic room with a skylight on offer. "
                       "Central, green and quiet, a short ride to HSG.",
        "photo_path": "assets/demo/wg_altbau_collage.jpg", "is_verified": 1, "is_active": 1,
    })
    insert(conn, "wg_members", {"wg_id": wg_id, "user_id": owner, "is_main_tenant": 1})


# =============================================================================
# Main
# =============================================================================
def main() -> None:
    random.seed(RANDOM_SEED)
    database.reset_db()
    # One hash for every fake user (hashing is slow on purpose). Fine for test
    # data only – real users each get their own salt via auth.register_user.
    password_hash = auth.hash_password(DEMO_PASSWORD)
    today = datetime.date.today()

    # AI-generated: OpenAI Codex, 19.11.2026. Close the connection after seeding.
    with closing(database.get_connection()) as conn, conn:
        # --- 1. Seekers ---------------------------------------------------------
        seekers = {}  # user_id -> sliders
        for i in range(NUM_SEEKERS):
            first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
            sliders = random_sliders()
            user_id = make_user(
                conn, password_hash, "search_wg",
                f"{first.lower()}.{last.lower()}{i}@student.unisg.ch", first, sliders,
            )
            insert(conn, "search_criteria", {
                "user_id": user_id,
                "max_rent": random.choice([600, 700, 750, 800, 900, 1000]),
                "move_in_date": (today + datetime.timedelta(days=random.randint(14, 150))).isoformat(),
                "max_travel_time": random.choice([10, 15, 20, 25, 30]),
                "preferred_flatmate_gender": random.choice(["any", "any", "any", "women only", "men only"]),
                "smoker": int(random.random() < 0.15),
            })
            seekers[user_id] = sliders

        # --- 2. WGs with their members ------------------------------------------
        wg_ids = []
        for i in range(NUM_WGS):
            district = random.choice(DISTRICTS)
            lat, lon, minutes = DISTRICT_INFO.get(district, DEFAULT_DISTRICT_INFO)
            room_size = random.randint(10, 22)
            rent = round((450 + room_size * 18 + max(0, 25 - minutes) * 6 + random.randint(-60, 60)) / 10) * 10
            wg_id = insert(conn, "wgs", {
                "title": f"Room in {district}",
                "address": f"{random.choice(['Ober', 'Unter', 'Berg', 'See', 'Wald'])}strasse {random.randint(1, 80)}",
                "district": district,
                "postcode": "9000",
                "latitude": lat + random.uniform(-0.003, 0.003),
                "longitude": lon + random.uniform(-0.004, 0.004),
                "rent_chf": rent,
                "utilities_chf": random.choice([60, 80, 100]),
                "deposit_chf": rent * 2,
                "room_size_m2": room_size,
                "flat_size_m2": random.randint(60, 130),
                "num_rooms": random.choice([3, 3.5, 4, 4.5, 5]),
                "num_flatmates": random.randint(1, 3),
                "furnished": int(random.random() < 0.4),
                "private_bathroom": int(random.random() < 0.15),
                "balcony": int(random.random() < 0.5),
                "amenities": ",".join(random.sample(AMENITIES, k=random.randint(2, 5))),
                "available_from": (today + datetime.timedelta(days=random.randint(0, 120))).isoformat(),
                "min_rental_months": random.choice([0, 3, 6, 12]),
                "wg_type": random.choice(WG_TYPES),
                "smoking_allowed": random.choice(SMOKING_OPTIONS),
                "pets_allowed": int(random.random() < 0.2),
                "preferred_gender": random.choice(["any", "any", "women only", "men only"]),
                "travel_time_min": minutes + random.randint(-2, 3),
                "description": "Friendly WG close to public transport.",
                "is_verified": int(random.random() < 0.9),
            })
            # Members share a similar "WG vibe"
            vibe = random_sliders()
            for m in range(random.randint(1, 3)):
                first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
                member_id = make_user(
                    conn, password_hash, "offer_wg",
                    f"{first.lower()}.{last.lower()}.wg{i}{m}@student.unisg.ch", first,
                    random_sliders(base=vibe, spread=1.5),
                )
                insert(conn, "wg_members", {"wg_id": wg_id, "user_id": member_id, "is_main_tenant": int(m == 0)})
            wg_ids.append(wg_id)

        # --- 3. Demo users from the use cases -------------------------------------
        jonas_sliders = {"tidiness": 7, "sociability": 7, "noise_tolerance": 5, "guests": 5,
                         "sleep_rhythm": 5, "cooking_together": 8, "cleaning_schedule": 7, "time_at_home": 6}
        mia_sliders = {"tidiness": 8, "sociability": 6, "noise_tolerance": 4, "guests": 4,
                       "sleep_rhythm": 4, "cooking_together": 7, "cleaning_schedule": 8, "time_at_home": 5}
        ana_sliders = {"tidiness": 7, "sociability": 8, "noise_tolerance": 6, "guests": 4,
                       "sleep_rhythm": 6, "cooking_together": 9, "cleaning_schedule": 6, "time_at_home": 5}
        # If the group changed the sliders in config.py, fall back to random values
        if set(ana_sliders) != set(SLIDER_KEYS):
            jonas_sliders, mia_sliders, ana_sliders = random_sliders(), random_sliders(), random_sliders()

        lat, lon, _ = DISTRICT_INFO.get("Rotmonten", DEFAULT_DISTRICT_INFO)
        demo_wg = insert(conn, "wgs", {
            "title": "Bright room in Rotmonten, 6 min to HSG", "address": "Rotmontenstrasse 12",
            "district": "Rotmonten", "postcode": "9000", "latitude": lat, "longitude": lon,
            "rent_chf": 780, "utilities_chf": 80, "deposit_chf": 1560, "room_size_m2": 15,
            "flat_size_m2": 85, "num_rooms": 3.5, "num_flatmates": 2, "furnished": 0,
            "private_bathroom": 0, "balcony": 1, "amenities": "Washing machine,Dishwasher,Wi-Fi",
            "available_from": (today + datetime.timedelta(days=60)).isoformat(), "min_rental_months": 6,
            "wg_type": WG_TYPES[-1], "smoking_allowed": SMOKING_OPTIONS[0], "pets_allowed": 0,
            "preferred_gender": "any", "travel_time_min": 6,
            "description": "We cook together a few times a week and keep the flat tidy.", "is_verified": 1,
        })
        jonas = make_user(conn, password_hash, "offer_wg", "jonas.demo@student.unisg.ch", "Jonas", jonas_sliders,
                          birth_year=2001, gender="male", study_level="Master",
                          bio="Master's student, main tenant, loves cooking.")
        mia = make_user(conn, password_hash, "offer_wg", "mia.demo@student.unisg.ch", "Mia", mia_sliders,
                        birth_year=2003, gender="female", study_level="Bachelor")
        insert(conn, "wg_members", {"wg_id": demo_wg, "user_id": jonas, "is_main_tenant": 1})
        insert(conn, "wg_members", {"wg_id": demo_wg, "user_id": mia, "is_main_tenant": 0})
        wg_ids.append(demo_wg)

        ana = make_user(conn, password_hash, "search_wg", "ana.demo@student.unisg.ch", "Ana", ana_sliders,
                        birth_year=2005, gender="female", languages="PT,EN", study_level="Exchange",
                        bio="Exchange student from Porto, starting at HSG in February.")
        insert(conn, "search_criteria", {
            "user_id": ana, "max_rent": 800, "max_travel_time": 20,
            "move_in_date": (today + datetime.timedelta(days=75)).isoformat(),
            "preferred_flatmate_gender": "any", "smoker": 0,
        })

        # --- 3c. Named test accounts (test_accounts.txt) --------------------------
        add_named_test_accounts(conn, today)
        add_photo_wg(conn, today)

        # --- 4. Swipes and matches --------------------------------------------------
        profiles = {wg_id: wg_profile(conn, wg_id) for wg_id in wg_ids}
        for seeker_id, sliders in seekers.items():
            for wg_id in random.sample(wg_ids, k=12):
                fit = similarity(sliders, profiles[wg_id])
                seeker_likes = random.random() < fit
                insert(conn, "swipes", {"seeker_id": seeker_id, "wg_id": wg_id, "swiped_by": "seeker",
                                        "liked": int(seeker_likes)})
                if seeker_likes and random.random() < 0.6:
                    wg_likes = random.random() < fit
                    insert(conn, "swipes", {"seeker_id": seeker_id, "wg_id": wg_id, "swiped_by": "wg",
                                            "liked": int(wg_likes)})
                    if wg_likes:
                        insert(conn, "matches", {"seeker_id": seeker_id, "wg_id": wg_id})

        # --- 5. Resolve matches into real outcomes (the ML training labels) ---------
        # Each match is viewed, then either accepted (both sides said yes) or
        # declined. More similar seeker/WG pairs are likelier to be accepted, so
        # the model can learn which lifestyle factors drive a successful match.
        # Each match is resolved independently (clean training labels).
        for match in conn.execute("SELECT match_id, seeker_id, wg_id FROM matches").fetchall():
            fit = similarity(seekers[match["seeker_id"]], profiles[match["wg_id"]])
            conn.execute("UPDATE matches SET viewing_done = 1 WHERE match_id = ?", (match["match_id"],))
            accept_probability = max(0.05, min(0.95, 0.5 + (fit - 0.69) * 4.0))  # similar -> accepted, with noise
            status = "accepted" if random.random() < accept_probability else "declined"
            conn.execute("UPDATE matches SET status = ? WHERE match_id = ?", (status, match["match_id"]))

    # --- Summary -------------------------------------------------------------------
    # AI-generated: OpenAI Codex, 19.11.2026. Close the summary connection too.
    with closing(database.get_connection()) as conn:
        for table in ["users", "search_criteria", "wgs", "wg_members", "swipes", "matches"]:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table:<16} {count:>4} rows")
        resolved = conn.execute(
            "SELECT status, COUNT(*) FROM matches WHERE status IN ('accepted','declined') GROUP BY status"
        ).fetchall()
        print("  resolved matches (ML labels): " + ", ".join(f"{s}={c}" for s, c in resolved))
    print(f"\nDone. Log in with e.g. ana.demo@student.unisg.ch / {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
