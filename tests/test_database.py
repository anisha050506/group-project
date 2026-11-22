"""Database integration checks using a temporary SQLite file."""

# AI-generated: OpenAI Codex, 19.11.2026. Prompt: validate the SQLite database
# and in-memory example against complete project workflows.
import contextlib
import io
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import database
from core.config import SLIDER_KEYS


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.db_path = patch.object(database, "DB_PATH", str(Path(self.temp_dir.name) / "test.db"))
        self.db_path.start()
        self.addCleanup(self.db_path.stop)
        database.init_db()
        self.seeker = database.create_user("ana@student.unisg.ch", "test-hash", "search_wg", "Ana")
        self.owner = database.create_user("jonas@student.unisg.ch", "test-hash", "offer_wg", "Jonas")
        self.member = database.create_user("mia@student.unisg.ch", "test-hash", "offer_wg", "Mia")
        self.wg = database.create_wg({"title": "Test WG", "is_verified": 1}, self.owner)
        database.add_wg_member(self.wg, self.member)

    def test_accounts_profiles_and_null_values(self):
        self.assertEqual(database.get_user_by_email(" ANA@student.unisg.ch ")["user_id"], self.seeker)
        self.assertIsNone(database.get_user_by_email("missing@student.unisg.ch"))
        self.assertIsNone(database.get_user_by_id(-1))
        database.update_profile(self.seeker, {"name": "Null", "bio": None, "tidiness": 0})
        row = database.get_user_by_id(self.seeker)
        self.assertEqual(row["name"], "Null")
        self.assertIsNone(row["bio"])
        self.assertEqual(row["tidiness"], 0)
        database.update_profile(self.seeker, {"name": "O'Brien"})
        self.assertEqual(database.get_user_by_id(self.seeker)["name"], "O'Brien")
        database.update_profile(self.seeker, {})
        with self.assertRaises(ValueError):
            database.update_profile(self.seeker, {"name = 'bad'; DROP TABLE users; --": "x"})
        with self.assertRaises(sqlite3.IntegrityError):
            database.create_user("ANA@student.unisg.ch", "test-hash", "search_wg", "Duplicate")
        with self.assertRaises(sqlite3.IntegrityError):
            database.update_role(self.seeker, "invalid")
        database.update_role(self.seeker, "offer_wg")
        self.assertEqual(database.get_user_by_id(self.seeker)["role"], "offer_wg")

    def test_criteria_upsert_preserves_unsupplied_fields(self):
        self.assertIsNone(database.get_search_criteria(self.seeker))
        self.assertEqual(database.get_all_seekers()[0]["user_id"], self.seeker)
        database.save_search_criteria(self.seeker, {"max_rent": 800, "smoker": 0})
        database.save_search_criteria(self.seeker, {"max_rent": 900})
        database.save_search_criteria(self.seeker, {})
        row = database.get_search_criteria(self.seeker)
        self.assertEqual(row["max_rent"], 900)
        self.assertEqual(row["smoker"], 0)
        self.assertEqual(database.get_all_seekers()[0]["max_rent"], 900)
        with self.assertRaises(ValueError):
            database.save_search_criteria(self.seeker, {"user_id": self.owner})

    def test_wgs_members_and_profile_averages(self):
        self.assertEqual(database.get_wg_for_user(self.owner)["wg_id"], self.wg)
        self.assertIsNone(database.get_wg_for_user(self.seeker))
        self.assertIsNone(database.get_wg(-1))
        members = database.get_wg_members(self.wg)
        self.assertEqual([row["user_id"] for row in members], [self.owner, self.member])
        self.assertEqual(members[0]["is_main_tenant"], 1)
        database.add_wg_member(self.wg, self.member)
        self.assertEqual(len(database.get_wg_members(self.wg)), 2)
        self.assertEqual([wg["wg_id"] for wg in database.get_all_active_wgs()], [self.wg])
        database.update_wg(self.wg, {"is_active": 0})
        self.assertEqual(database.get_all_active_wgs(), [])
        database.update_wg(self.wg, {"is_active": 1, "is_verified": 0})
        self.assertEqual(database.get_all_active_wgs(), [])
        self.assertTrue(all(value is None for value in database.get_wg_lifestyle_profile(self.wg).values()))
        database.update_profile(self.owner, {"tidiness": 0, "sociability": 8})
        database.update_profile(self.member, {"tidiness": 10})
        profile = database.get_wg_lifestyle_profile(self.wg)
        self.assertEqual(profile["tidiness"], 5.0)
        self.assertEqual(profile["sociability"], 8.0)

    def test_wg_creation_rolls_back_when_owner_is_missing(self):
        with self.assertRaises(sqlite3.IntegrityError):
            database.create_wg({"title": "Orphan"}, -1)
        with contextlib.closing(database.get_connection()) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM wgs").fetchone()[0], 1)

    def test_swipes_make_one_match_and_filter_responses(self):
        self.assertFalse(database.save_swipe(self.seeker, self.wg, "seeker", True))
        self.assertEqual(database.get_swiped_wg_ids(self.seeker), [self.wg])
        self.assertEqual(database.get_seekers_who_liked_wg(self.wg)[0]["user_id"], self.seeker)
        self.assertTrue(database.save_swipe(self.seeker, self.wg, "wg", True))
        self.assertEqual(database.get_seekers_who_liked_wg(self.wg), [])
        self.assertFalse(database.save_swipe(self.seeker, self.wg, "wg", True))
        for user_id in (self.seeker, self.owner, self.member):
            self.assertEqual(len(database.get_matches_for_user(user_id)), 1)
        match = database.get_matches_for_user(self.seeker)[0]
        database.update_match(match["match_id"], {"status": "offered", "viewing_done": 1})
        self.assertEqual(database.get_matches_for_user(self.seeker)[0]["status"], "offered")
        with self.assertRaises(ValueError):
            database.update_match(match["match_id"], {"status": "invalid"})
        with self.assertRaises(ValueError):
            database.save_swipe(self.seeker, self.wg, "invalid", True)

    def test_provider_first_and_pass_do_not_create_premature_matches(self):
        self.assertFalse(database.save_swipe(self.seeker, self.wg, "wg", True))
        self.assertEqual(database.get_swiped_wg_ids(self.seeker), [])
        self.assertFalse(database.save_swipe(self.seeker, self.wg, "seeker", False))
        self.assertEqual(database.get_matches_for_user(self.seeker), [])
        self.assertTrue(database.save_swipe(self.seeker, self.wg, "seeker", True))

    def test_chat_is_ordered_and_requires_a_participant(self):
        database.save_swipe(self.seeker, self.wg, "seeker", True)
        database.save_swipe(self.seeker, self.wg, "wg", True)
        match_id = database.get_matches_for_user(self.seeker)[0]["match_id"]
        outsider = database.create_user("other@student.unisg.ch", "test-hash", "search_wg", "Other")
        self.assertEqual(database.get_matches_for_user(outsider), [])
        with self.assertRaises(ValueError):
            database.send_message(match_id, outsider, "Not my match")
        database.send_message(match_id, self.seeker, "Can I visit?")
        database.send_message(match_id, self.member, "Yes, Saturday!")
        messages = database.get_messages(match_id)
        self.assertEqual([row["text"] for row in messages], ["Can I visit?", "Yes, Saturday!"])
        self.assertEqual(messages[1]["sender_name"], "Mia")

    def test_training_data_has_one_row_per_resolved_match_and_correct_averages(self):
        empty = database.get_training_data()
        self.assertTrue(empty.empty)
        self.assertIn("matched", empty.columns)
        database.update_profile(self.seeker, {key: 7 for key in SLIDER_KEYS})
        database.update_profile(self.owner, {key: 4 for key in SLIDER_KEYS})
        database.update_profile(self.member, {key: 8 for key in SLIDER_KEYS})
        # self.wg members: owner (4) + member (8) -> average 6.0; a second WG has owner only -> 4.0.
        wg2 = database.create_wg({"title": "WG2", "is_verified": 1}, self.owner)
        with contextlib.closing(database.get_connection()) as conn, conn:
            conn.execute("INSERT INTO matches (seeker_id, wg_id, status) VALUES (?, ?, 'accepted')", (self.seeker, self.wg))
            conn.execute("INSERT INTO matches (seeker_id, wg_id, status) VALUES (?, ?, 'declined')", (self.seeker, wg2))
            # An open match is still undecided and must not appear as training data.
            conn.execute("INSERT INTO matches (seeker_id, wg_id, status) VALUES (?, ?, 'open')", (self.member, self.wg))
        training = database.get_training_data()
        self.assertEqual(len(training), 2)
        self.assertEqual(training["matched"].tolist(), [1, 0])  # accepted first (lower match_id), then declined
        for key in SLIDER_KEYS:
            self.assertEqual(training[f"seeker_{key}"].tolist(), [7, 7])
            self.assertEqual(training[f"wg_{key}"].tolist(), [6.0, 4.0])
        # A WG with no members has unknown (NaN) lifestyle averages.
        empty_wg = database.create_wg({}, self.owner)
        with contextlib.closing(database.get_connection()) as conn, conn:
            conn.execute("DELETE FROM wg_members WHERE wg_id = ?", (empty_wg,))
            conn.execute("INSERT INTO matches (seeker_id, wg_id, status) VALUES (?, ?, 'declined')", (self.seeker, empty_wg))
        self.assertTrue(database.get_training_data()["wg_tidiness"].isna().iloc[-1])

    def test_existing_seed_script_and_repeated_initialization(self):
        from data import seed_data

        with contextlib.redirect_stdout(io.StringIO()):
            seed_data.main()
        database.init_db()
        # 60 random seekers + Ana (demo) + 8 named test seekers (test_accounts.txt)
        self.assertEqual(len(database.get_all_seekers()), 69)
        # Training data = resolved matches (accepted/declined), with both outcomes present.
        training = database.get_training_data()
        self.assertGreater(len(training), 50)
        self.assertEqual(sorted(training["matched"].unique().tolist()), [0, 1])
        self.assertFalse(training.isna().any().any())
        with contextlib.closing(database.get_connection()) as conn:
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(conn.execute("PRAGMA integrity_check").fetchone()[0], "ok")


class ExampleDatabaseTests(unittest.TestCase):
    def test_all_tables_have_valid_related_sample_rows(self):
        from core.auth import verify_password
        from data.database_example import DB

        self.addCleanup(DB.close)
        tables = {row[0] for row in DB.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        )}
        self.assertEqual(tables, {
            "users", "search_criteria", "wgs", "wg_members", "swipes", "matches", "messages", "feedback", "conversation_reads",
        })
        for table in tables:
            self.assertGreater(DB.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], 0)
        self.assertEqual(DB.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertIsNone(DB.execute("SELECT bio FROM users WHERE name = 'Mia'").fetchone()[0])
        for (password_hash,) in DB.execute("SELECT password_hash FROM users"):
            self.assertTrue(verify_password("demo1234", password_hash))


if __name__ == "__main__":
    unittest.main()
