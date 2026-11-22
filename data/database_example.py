"""All project tables with small sample datasets, in the requested format.

Run from the repository root: python -m data.database_example
Or import DB and query it with pd.read_sql_query("SELECT * FROM users", DB).
This database exists only in memory and does not change data/wg_match.db.
All sample accounts use the password demo1234.
"""

# AI-generated: OpenAI Codex, 19.11.2026. Prompt: make the database for
# everything in the supplied sqlite3 / pandas / DB.executescript format.
import sqlite3
import pandas as pd

from core.database import SCHEMA

DB = sqlite3.connect(":memory:")
DB.execute("PRAGMA foreign_keys = ON")

# SCHEMA contains every CREATE TABLE statement, defined in core/database.py.
# The INSERT statements below run together with those CREATE statements.
DB.executescript(SCHEMA + '''
    INSERT INTO users (
        user_id, email, password_hash, role, name, birth_year, gender,
        languages, study_level, bio, is_verified,
        tidiness, sociability, noise_tolerance, guests, sleep_rhythm,
        cooking_together, cleaning_schedule, time_at_home
    ) VALUES
        (1, 'ana.demo@student.unisg.ch',
         'demo$bcc93b3f315ce44b4dec09dbbe9d360f457b2386dcd8e1ef4fb53f3d18448389',
         'search_wg', 'Ana', 2005, 'female', 'PT,EN', 'Exchange',
         'Exchange student from Porto.', 1, 7, 8, 6, 4, 6, 9, 6, 5),
        (2, 'jonas.demo@student.unisg.ch',
         'demo$bcc93b3f315ce44b4dec09dbbe9d360f457b2386dcd8e1ef4fb53f3d18448389',
         'offer_wg', 'Jonas', 2001, 'male', 'DE,EN', 'Master',
         'Main tenant, loves cooking.', 1, 7, 7, 5, 5, 5, 8, 7, 6),
        (3, 'mia.demo@student.unisg.ch',
         'demo$bcc93b3f315ce44b4dec09dbbe9d360f457b2386dcd8e1ef4fb53f3d18448389',
         'offer_wg', 'Mia', 2003, 'female', 'DE,EN', 'Bachelor',
         NULL, 1, 8, 6, 4, 4, 4, 7, 8, 5);  -- bio unknown

    INSERT INTO search_criteria (
        user_id, max_rent, move_in_date, max_travel_time,
        preferred_flatmate_gender, smoker
    ) VALUES
        (1, 800, '2027-02-01', 20, 'any', 0);

    INSERT INTO wgs (
        wg_id, title, address, district, postcode, latitude, longitude,
        rent_chf, utilities_chf, deposit_chf, room_size_m2, flat_size_m2,
        num_rooms, num_flatmates, furnished, private_bathroom, balcony,
        amenities, available_from, available_until, min_rental_months,
        wg_type, smoking_allowed, pets_allowed, preferred_gender,
        travel_time_min, description, is_verified, is_active
    ) VALUES
        (1, 'Bright room in Rotmonten, 6 min to HSG', 'Rotmontenstrasse 12',
         'Rotmonten', '9000', 47.4335, 9.3800,
         780, 80, 1560, 15, 85, 3.5, 2, 0, 0, 1,
         'Washing machine,Dishwasher,Wi-Fi', '2027-01-15', NULL, 6,
         'Social WG', 'No', 0, 'any', 6,
         'We cook together and keep the flat tidy.', 1, 1);
         -- available_until NULL means no fixed end date

    INSERT INTO wg_members (wg_id, user_id, is_main_tenant) VALUES
        (1, 2, 1),
        (1, 3, 0);

    INSERT INTO swipes (swipe_id, seeker_id, wg_id, swiped_by, liked) VALUES
        (1, 1, 1, 'seeker', 1),
        (2, 1, 1, 'wg', 1);

    INSERT INTO matches (match_id, seeker_id, wg_id, status, viewing_done) VALUES
        (1, 1, 1, 'accepted', 1);

    INSERT INTO messages (message_id, match_id, sender_id, text) VALUES
        (1, 1, 1, 'Hi! Could I visit the room?'),
        (2, 1, 2, 'Yes, Saturday at 14:00 works for us.');

    -- AI-generated: OpenAI Codex, 19.11.2026. Sample durable chat read positions.
    INSERT INTO conversation_reads (match_id, user_id, last_read_message_id) VALUES
        (1, 1, 2),
        (1, 2, 1);
''')


if __name__ == "__main__":
    for table in (
        "users", "search_criteria", "wgs", "wg_members", "swipes", "matches",
        "messages", "conversation_reads",
    ):
        print(f"\n{table}")
        # Show profile data without printing account password hashes.
        columns = "user_id, name, role, bio" if table == "users" else "*"
        print(pd.read_sql_query(f"SELECT {columns} FROM {table}", DB).to_string(index=False))
    DB.close()
