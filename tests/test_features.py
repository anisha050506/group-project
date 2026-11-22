"""Service and Streamlit integration tests, using isolated databases/models."""
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: code everything missing.
import contextlib
import io
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import requests
from PIL import Image
from streamlit.testing.v1 import AppTest

from core import auth, database, matching, ml_model, transport_api, uploads
from core.config import SLIDER_KEYS


class FeatureFixture(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        for target, name, value in (
            (database, "DB_PATH", str(self.root / "test.db")),
            (ml_model, "MODEL_PATH", str(self.root / "model.pkl")),
            (uploads, "UPLOAD_DIR", self.root / "uploads"),
        ):
            patcher = patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        database.init_db()
        password_hash = auth.hash_password("password123")
        self.seeker = database.create_user("ana@student.unisg.ch", password_hash, "search_wg", "Ana")
        self.owner = database.create_user("jonas@student.unisg.ch", password_hash, "offer_wg", "Jonas")
        self.member = database.create_user("mia@student.unisg.ch", password_hash, "offer_wg", "Mia")
        for user_id in (self.seeker, self.owner, self.member):
            database.update_profile(user_id, {**{key: 7 for key in SLIDER_KEYS}, "is_verified": 1, "gender": "female" if user_id != self.owner else "male"})
        self.wg = database.create_wg({
            "title": "Sunny room", "address": "Teststrasse 12", "district": "Rotmonten", "postcode": "9000",
            "rent_chf": 780, "room_size_m2": 15, "flat_size_m2": 85, "num_flatmates": 2,
            "travel_time_min": 6, "latitude": 47.43, "longitude": 9.38,
            "available_from": (date.today() + timedelta(days=10)).isoformat(),
            "preferred_gender": "any", "smoking_allowed": "No", "is_verified": 1,
        }, self.owner)
        database.add_wg_member(self.wg, self.member)
        self.criteria = {
            "max_rent": 800, "max_travel_time": 20, "move_in_date": (date.today() + timedelta(days=30)).isoformat(),
            "preferred_flatmate_gender": "any", "smoker": 0,
        }
        database.save_search_criteria(self.seeker, self.criteria)

    def new_match(self, seeker_id=None):
        seeker_id = seeker_id or self.seeker
        database.save_swipe(seeker_id, self.wg, "seeker", True)
        database.save_swipe(seeker_id, self.wg, "wg", True)
        return next(row["match_id"] for row in database.get_matches_for_user(seeker_id) if row["seeker_id"] == seeker_id)

    def app(self, email="ana@student.unisg.ch", password="password123"):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
        app.text_input[0].input(email)
        app.text_input[1].input(password)
        self.click(app, "Log in")
        self.no_errors(app)
        return app

    def click(self, app, label):
        next(button for button in app.button if button.label == label).click().run()
        self.no_errors(app)

    def no_errors(self, app):
        self.assertEqual([error.message for error in app.exception], [])


class AuthTests(FeatureFixture):
    def test_registration_login_and_duplicates(self):
        success, _ = auth.register_user(" NEW@student.unisg.ch ", "password123", "password123", " New ", "search_wg")
        self.assertTrue(success)
        user = auth.login_user("new@student.unisg.ch", "password123")
        self.assertEqual(user["name"], "New")
        self.assertNotEqual(user["password_hash"], "password123")
        self.assertEqual(user["is_verified"], 1)
        self.assertIsNone(auth.login_user("new@student.unisg.ch", "wrong"))
        self.assertFalse(auth.register_user("new@student.unisg.ch", "password123", "password123", "New", "offer_wg")[0])
        self.assertFalse(auth.verify_password("password123", "malformed"))

    def test_registration_rejects_invalid_input(self):
        for email in ("@student.unisg.ch", "a@@student.unisg.ch", "a b@student.unisg.ch", "a@student.unisg.ch.evil", "a@gmail.com"):
            self.assertFalse(auth.is_valid_hsg_email(email))
        for password, repeat, name, role in (
            ("short", "short", "New", "search_wg"),
            ("password123", "different", "New", "search_wg"),
            ("password123", "password123", " ", "search_wg"),
            ("password123", "password123", "New", "invalid"),
        ):
            self.assertFalse(auth.register_user("new@student.unisg.ch", password, repeat, name, role)[0])
        self.assertIsNone(database.get_user_by_email("new@student.unisg.ch"))


class MatchingTests(FeatureFixture):
    # AI-generated: OpenAI Codex, 19.11.2026. Prompt: diagnose Cyril and Jack's WG and let either side swipe first.
    def test_provider_can_swipe_first_and_mutual_like_creates_one_match(self):
        self.assertEqual([row["user_id"] for row in matching.rank_seekers_for_wg(self.wg)], [self.seeker])
        self.assertFalse(database.save_swipe(self.seeker, self.wg, "wg", True))
        self.assertEqual(database.get_matches_for_user(self.owner), [])
        self.assertEqual(matching.rank_seekers_for_wg(self.wg), [])
        self.assertEqual([row["wg_id"] for row in matching.rank_wgs_for_seeker(self.seeker)], [self.wg])
        self.assertTrue(database.save_swipe(self.seeker, self.wg, "seeker", True))
        self.assertFalse(database.save_swipe(self.seeker, self.wg, "seeker", True))
        self.assertEqual(len(database.get_matches_for_user(self.owner)), 1)

    def test_provider_excludes_own_members_and_previously_passed_seekers(self):
        database.update_role(self.member, "search_wg")
        database.save_search_criteria(self.member, self.criteria)
        self.assertEqual([row["user_id"] for row in matching.rank_seekers_for_wg(self.wg)], [self.seeker])
        database.save_swipe(self.seeker, self.wg, "wg", False)
        self.assertEqual(matching.rank_seekers_for_wg(self.wg), [])
        exclusions = {row["name"]: row["reasons"] for row in matching.swipe_exclusions(self.owner)}
        self.assertIn("The seeker already belongs to this WG.", exclusions["Mia"])
        self.assertIn("You have already liked or passed this candidate.", exclusions["Ana"])

    def test_cyril_and_jack_data_explain_both_blockers_before_swiping(self):
        # Reproduce the reported saved settings in the isolated test database.
        database.update_profile(self.seeker, {"name": "Cyril", "gender": "female"})
        database.update_profile(self.owner, {"name": "Jack"})
        database.update_wg(self.wg, {"title": "Jack's WG", "preferred_gender": "men only", "travel_time_min": None})
        database.save_search_criteria(self.seeker, {"max_rent": 2000, "max_travel_time": 60})
        self.assertEqual(matching.rank_seekers_for_wg(self.wg), [])
        self.assertEqual(matching.rank_wgs_for_seeker(self.seeker), [])
        for user_id, candidate_name in ((self.owner, "Cyril"), (self.seeker, "Jack's WG")):
            reasons = next(row["reasons"] for row in matching.swipe_exclusions(user_id) if row["name"] == candidate_name)
            self.assertTrue(any("travel time to HSG is unknown" in reason for reason in reasons))
            self.assertTrue(any("men only" in reason and "female" in reason for reason in reasons))
        database.update_profile(self.seeker, {"gender": "male"})
        self.assertEqual(matching.rank_seekers_for_wg(self.wg), [])
        database.update_wg(self.wg, {"travel_time_min": 20})
        self.assertEqual(matching.swipe_exclusions(self.seeker), [])
        self.assertEqual([row["user_id"] for row in matching.rank_seekers_for_wg(self.wg)], [self.seeker])
        self.assertEqual([row["wg_id"] for row in matching.rank_wgs_for_seeker(self.seeker)], [self.wg])

    def test_filters_budget_dates_travel_smoking_and_both_gender_preferences(self):
        seeker, wg = database.get_user_by_id(self.seeker), database.get_wg(self.wg)
        self.assertTrue(matching.passes_hard_filters(seeker, self.criteria, wg))
        for changes in ({"rent_chf": 801}, {"rent_chf": None}, {"travel_time_min": 21}, {"travel_time_min": None},
                        {"available_from": "2099-01-01"}, {"available_from": None}, {"available_until": date.today().isoformat()}, {"preferred_gender": "men only"}):
            self.assertFalse(matching.passes_hard_filters(seeker, self.criteria, {**wg, **changes}), changes)
        self.assertFalse(matching.passes_hard_filters(seeker, {**self.criteria, "smoker": 1}, wg))
        self.assertTrue(matching.passes_hard_filters(seeker, {**self.criteria, "smoker": 1}, {**wg, "smoking_allowed": "Balcony only"}))
        self.assertFalse(matching.passes_hard_filters(seeker, {**self.criteria, "preferred_flatmate_gender": "women only"}, wg))
        database.update_profile(self.owner, {"gender": "female"})
        self.assertTrue(matching.passes_hard_filters(seeker, {**self.criteria, "preferred_flatmate_gender": "women only"}, wg))

    def test_scores_missing_answers_and_ranking(self):
        zeros, tens = {key: 0 for key in SLIDER_KEYS}, {key: 10 for key in SLIDER_KEYS}
        self.assertEqual(matching.compatibility_score(zeros, zeros), 100)
        self.assertEqual(matching.compatibility_score(zeros, tens), 0)
        self.assertEqual(matching.compatibility_score({}, {}), 0)
        self.assertTrue(matching.profile_is_complete(zeros))
        self.assertFalse(matching.profile_is_complete({}))
        self.assertEqual(len(matching.biggest_mismatches(zeros, tens, 2)), 2)
        ranked = matching.rank_wgs_for_seeker(self.seeker)
        self.assertEqual([row["wg_id"] for row in ranked], [self.wg])
        self.assertEqual(ranked[0]["score"], 100)
        database.save_swipe(self.seeker, self.wg, "seeker", True)
        self.assertEqual(matching.rank_wgs_for_seeker(self.seeker), [])
        self.assertEqual(matching.rank_seekers_for_wg(self.wg)[0]["user_id"], self.seeker)
        database.save_swipe(self.seeker, self.wg, "wg", False)
        self.assertEqual(matching.rank_seekers_for_wg(self.wg), [])


class WorkflowTests(FeatureFixture):
    # AI-generated: OpenAI Codex, 19.11.2026. Prompt: live chat inbox with durable unread counts.
    def test_conversation_unread_counts_are_per_user_and_race_safe(self):
        match_id = self.new_match()
        database.send_message(match_id, self.seeker, "Hello")
        first_id = database.get_messages(match_id)[-1]["message_id"]
        database.send_message(match_id, self.owner, "Welcome!")
        self.assertEqual(database.get_conversations_for_user(self.owner)[0]["unread_count"], 1)
        self.assertEqual(database.get_conversations_for_user(self.seeker)[0]["unread_count"], 1)
        self.assertEqual(database.get_conversations_for_user(self.member)[0]["unread_count"], 2)
        # A new message arriving after the displayed snapshot stays unread.
        database.send_message(match_id, self.seeker, "Can I visit tomorrow?")
        database.mark_conversation_read(match_id, self.owner, first_id)
        self.assertEqual(database.get_conversations_for_user(self.owner)[0]["unread_count"], 1)
        latest_id = database.get_messages(match_id)[-1]["message_id"]
        database.mark_conversation_read(match_id, self.owner, latest_id)
        database.mark_conversation_read(match_id, self.owner, first_id)
        self.assertEqual(database.get_conversations_for_user(self.owner)[0]["unread_count"], 0)
        self.assertEqual(database.get_conversations_for_user(self.member)[0]["unread_count"], 3)
        outsider = database.create_user("outsider@student.unisg.ch", "hash", "search_wg", "Outsider")
        self.assertEqual(database.get_conversations_for_user(outsider), [])
        with self.assertRaises(ValueError):
            database.mark_conversation_read(match_id, outsider, latest_id)

    def test_notification_counts_track_new_matches_and_unread_messages(self):
        # A fresh match with no chat counts as a new-match notification for both sides.
        match_id = self.new_match()
        for user_id in (self.seeker, self.owner, self.member):
            counts = database.get_notification_counts(user_id)
            self.assertEqual((counts["new_matches"], counts["unread_messages"]), (1, 0))
        # Once a message exists it is no longer a "new match"; recipients see unread.
        database.send_message(match_id, self.owner, "Welcome!")
        self.assertEqual(database.get_notification_counts(self.owner),
                         {"new_matches": 0, "unread_messages": 0, "total": 0})
        self.assertEqual(database.get_notification_counts(self.seeker),
                         {"new_matches": 0, "unread_messages": 1, "total": 1})
        # Reading the conversation clears the unread notification.
        latest_id = database.get_messages(match_id)[-1]["message_id"]
        database.mark_conversation_read(match_id, self.seeker, latest_id)
        self.assertEqual(database.get_notification_counts(self.seeker)["total"], 0)
        # Someone with no matches has nothing to notify.
        outsider = database.create_user("nobody@student.unisg.ch", "hash", "search_wg", "Nobody")
        self.assertEqual(database.get_notification_counts(outsider)["total"], 0)

    def test_undo_last_swipe_removes_like_and_open_match_but_keeps_chatted_ones(self):
        database.save_swipe(self.seeker, self.wg, "seeker", True)
        database.undo_last_swipe(self.seeker, self.wg, "seeker")
        self.assertEqual(database.get_swiped_wg_ids(self.seeker), [])
        # Undoing the like that made a match removes that still-open match.
        match_id = self.new_match()
        database.undo_last_swipe(self.seeker, self.wg, "wg")
        self.assertEqual(database.get_matches_for_user(self.seeker), [])
        # A match with messages is preserved even if a swipe is undone.
        match_id = self.new_match()
        database.send_message(match_id, self.owner, "Hi")
        database.undo_last_swipe(self.seeker, self.wg, "wg")
        self.assertEqual(len(database.get_matches_for_user(self.seeker)), 1)

    def test_conversations_sort_by_latest_activity_and_show_preview(self):
        first_match = self.new_match()
        other = database.create_user("bea@student.unisg.ch", "hash", "search_wg", "Bea")
        second_match = self.new_match(other)
        database.send_message(second_match, other, "Second conversation")
        database.send_message(first_match, self.seeker, "Newest message")
        inbox = database.get_conversations_for_user(self.owner)
        self.assertEqual([row["match_id"] for row in inbox], [first_match, second_match])
        self.assertEqual(inbox[0]["last_message_text"], "Newest message")
        self.assertEqual(inbox[0]["last_sender_name"], "Ana")

    def test_offer_permissions_and_acceptance_close_competing_matches(self):
        match_id = self.new_match()
        other = database.create_user("other@student.unisg.ch", "hash", "search_wg", "Other")
        other_match = self.new_match(other)
        with self.assertRaises(ValueError):
            database.change_match_status(match_id, self.owner, "offered")
        with self.assertRaises(ValueError):
            database.mark_viewing_done(match_id, other)
        database.mark_viewing_done(match_id, self.member)
        with self.assertRaises(ValueError):
            database.change_match_status(match_id, self.member, "offered")
        database.change_match_status(match_id, self.owner, "offered")
        with self.assertRaises(ValueError):
            database.change_match_status(match_id, self.owner, "accepted")
        database.change_match_status(match_id, self.seeker, "accepted")
        self.assertEqual(database.get_wg(self.wg)["is_active"], 0)
        self.assertEqual(next(row for row in database.get_matches_for_user(other) if row["match_id"] == other_match)["status"], "declined")
        with self.assertRaises(ValueError):
            database.save_swipe(other, self.wg, "seeker", True)
        with self.assertRaises(ValueError):
            database.change_match_status(other_match, other, "accepted")
        self.assertEqual(matching.rank_wgs_for_seeker(self.seeker), [])

    def test_accepted_match_is_training_data_and_member_removal(self):
        match_id = self.new_match()
        database.mark_viewing_done(match_id, self.owner)
        database.change_match_status(match_id, self.owner, "offered")
        database.change_match_status(match_id, self.seeker, "accepted")
        # An accepted match is one positive (matched = 1) training row.
        training = database.get_training_data()
        self.assertEqual(len(training), 1)
        self.assertEqual(training["matched"].iloc[0], 1)
        with self.assertRaises(ValueError):
            database.send_message(match_id, self.seeker, "  ")
        with self.assertRaises(ValueError):
            database.remove_wg_member(self.wg, self.member, self.seeker)
        database.remove_wg_member(self.wg, self.member, self.owner)
        self.assertEqual(len(database.get_wg_members(self.wg)), 1)


class TransportTests(unittest.TestCase):
    def test_duration_and_fastest_connection(self):
        self.assertEqual(transport_api.parse_duration("01d02:03:01"), 1564)
        with self.assertRaises(ValueError):
            transport_api.parse_duration("00d99:99:99")
        response = Mock()
        response.json.return_value = {"connections": [{"duration": "00d00:20:00"}, {"duration": "bad"}, {"duration": "00d00:14:01"}]}
        with patch.object(transport_api.requests, "get", return_value=response) as get:
            self.assertEqual(transport_api.get_travel_time_minutes("Rotmonten"), 15)
            self.assertEqual(get.call_args.kwargs["timeout"], 10)
        response.json.return_value = {"stations": [{"coordinate": {"x": 47.43, "y": 9.38}}]}
        with patch.object(transport_api.requests, "get", return_value=response):
            self.assertEqual(transport_api.get_location_coordinates("Rotmonten"), (47.43, 9.38))

    def test_network_and_invalid_response_failures(self):
        for exception in (requests.Timeout(), requests.ConnectionError(), ValueError("invalid JSON")):
            with patch.object(transport_api.requests, "get", side_effect=exception):
                self.assertIsNone(transport_api.get_travel_time_minutes("Rotmonten"))
                self.assertIsNone(transport_api.get_location_coordinates("Rotmonten"))
        response = Mock()
        for value in ({"connections": []}, {"connections": None}, None, {"connections": [{"duration": None}]}):
            response.json.return_value = value
            with patch.object(transport_api.requests, "get", return_value=response):
                self.assertIsNone(transport_api.get_travel_time_minutes("Rotmonten"))


class ModelAndPhotoTests(FeatureFixture):
    def test_seeded_model_training_saving_loading_and_prediction(self):
        from data import seed_data
        with contextlib.redirect_stdout(io.StringIO()):
            seed_data.main()
        metrics = ml_model.train_model()
        self.assertEqual(metrics["sample_rows"], len(database.get_training_data()))
        self.assertGreater(metrics["training_rows"], 0)
        self.assertGreater(metrics["test_rows"], 0)
        self.assertGreater(metrics["held_out_seekers"], 0)
        self.assertTrue(Path(ml_model.MODEL_PATH).exists())
        ml_model._read_bundle.cache_clear()
        user = database.get_user_by_email("ana.demo@student.unisg.ch")
        wg = database.get_wg_for_user(database.get_user_by_email("jonas.demo@student.unisg.ch")["user_id"])
        probability = ml_model.predict_match_probability(user, database.get_wg_lifestyle_profile(wg["wg_id"]))
        self.assertTrue(0 <= probability <= 1)
        self.assertEqual(ml_model.get_model_metrics(), metrics)
        self.assertIsNotNone(matching.rank_wgs_for_seeker(user["user_id"])[0]["ml_probability"])

    def test_model_without_training_data_and_corrupt_model(self):
        with self.assertRaises(ValueError):
            ml_model.train_model()
        Path(ml_model.MODEL_PATH).write_bytes(b"broken model")
        with self.assertRaises(ValueError):
            ml_model.load_model()
        self.assertEqual(matching.rank_wgs_for_seeker(self.seeker)[0]["score"], 100)

    def test_photos_are_validated_and_resized(self):
        upload = io.BytesIO()
        Image.new("RGB", (2000, 1000), "red").save(upload, "PNG")
        upload.size = len(upload.getvalue())
        filename = uploads.save_photo(upload, "user_1")
        with Image.open(filename) as image:
            self.assertEqual(image.format, "JPEG")
            self.assertEqual(image.size, (1600, 800))
        invalid = io.BytesIO(b"not an image")
        invalid.size = 12
        with self.assertRaises(ValueError):
            uploads.save_photo(invalid, "user_1")
        invalid.size = uploads.MAX_PHOTO_BYTES + 1
        with self.assertRaises(ValueError):
            uploads.save_photo(invalid, "user_1")


class ChatPresentationTests(unittest.TestCase):
    # AI-generated: OpenAI Codex, 19.11.2026. Verify literal messages and local day boundaries.
    def test_bubbles_escape_messages_names_and_headers(self):
        from components.chat import conversation_header_html, message_history_html
        html = message_history_html([{
            "sender_id": 2, "sender_name": "<img src=x>",
            "text": "<script>alert('x')</script>\nHello & welcome",
            "created_at": "2026-11-19 23:30:00",
        }], 1)
        self.assertNotIn("<script>", html)
        self.assertNotIn("<img src=x>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("Hello &amp; welcome", html)
        self.assertIn("00:30", html)
        header = conversation_header_html("<Room>", "<status>")
        self.assertIn("&lt;Room&gt;", header)
        self.assertNotIn("<status>", header)


class AppFlowTests(FeatureFixture):
    # AI-generated: OpenAI Codex, 19.11.2026. Prompt: async WhatsApp-style conversations.
    def test_inbox_schedules_live_updates_even_before_a_match_exists(self):
        from streamlit.testing.v1.local_script_runner import LocalScriptRunner
        original = LocalScriptRunner.forward_msgs
        schedules = []

        def record_schedules(runner):
            messages = original(runner)
            schedules.extend(message.auto_rerun for message in messages if message.HasField("auto_rerun"))
            return messages

        app = self.app()
        with patch.object(LocalScriptRunner, "forward_msgs", record_schedules):
            app.switch_page("views/matches.py").run()
        self.no_errors(app)
        self.assertTrue(any(schedule.interval == 2 and schedule.fragment_id for schedule in schedules))
        self.assertEqual(len(app.chat_input), 0)
        self.new_match()
        app.run()
        self.no_errors(app)
        self.assertEqual(len(app.chat_input), 1)

    def test_live_chat_two_sessions_refresh_without_duplicate_sends(self):
        match_id = self.new_match()
        seeker_app = self.app()
        seeker_app.switch_page("views/matches.py").run()
        owner_app = self.app("jonas@student.unisg.ch")
        owner_app.switch_page("views/matches.py").run()
        seeker_app.chat_input[0].set_value("Hello from Ana!").run()
        self.no_errors(seeker_app)
        self.assertEqual(database.get_conversations_for_user(self.owner)[0]["unread_count"], 1)
        owner_app.run()  # Simulate the next scheduled live-inbox tick.
        self.no_errors(owner_app)
        self.assertTrue(any("Hello from Ana!" in element.proto.body for element in owner_app.get("html")))
        self.assertEqual(database.get_conversations_for_user(self.owner)[0]["unread_count"], 0)
        owner_app.chat_input[0].set_value("Hi Ana, welcome!").run()
        seeker_app.run()
        self.no_errors(seeker_app)
        self.assertTrue(any("Hi Ana, welcome!" in element.proto.body for element in seeker_app.get("html")))
        seeker_app.run()
        self.assertEqual(len(database.get_messages(match_id)), 2)
        self.assertFalse(any(button.label == "Refresh conversation" for button in seeker_app.button))

    def test_inbox_switching_search_and_unread_badges(self):
        first_match = self.new_match()
        other = database.create_user("bea@student.unisg.ch", "hash", "search_wg", "Bea")
        second_match = self.new_match(other)
        database.send_message(first_match, self.seeker, "Hello from Ana")
        app = self.app("jonas@student.unisg.ch")
        app.switch_page("views/matches.py").run()
        self.assertEqual(app.session_state[f"active_chat_{self.owner}"], first_match)
        database.send_message(second_match, other, "Hello from Bea")
        app.run()
        self.no_errors(app)
        self.assertEqual(app.session_state[f"active_chat_{self.owner}"], first_match)
        bea_button = app.button(key=f"conversation_{self.owner}_{second_match}")
        self.assertIn("1 new", bea_button.label)
        bea_button.click().run()
        self.no_errors(app)
        self.assertEqual(app.session_state[f"active_chat_{self.owner}"], second_match)
        self.assertEqual(database.get_conversations_for_user(self.owner)[0]["unread_count"], 0)
        app.chat_input[0].set_value("Reply to Bea only").run()
        self.assertEqual(database.get_messages(first_match)[-1]["text"], "Hello from Ana")
        self.assertEqual(database.get_messages(second_match)[-1]["text"], "Reply to Bea only")
        app.text_input(key=f"chat_search_{self.owner}").input("Ana").run()
        self.no_errors(app)
        self.assertTrue(any(button.key == f"conversation_{self.owner}_{first_match}" for button in app.button))
        self.assertFalse(any(button.key == f"conversation_{self.owner}_{second_match}" for button in app.button))

    # AI-generated: OpenAI Codex, 19.11.2026. Prompt: fix two-sided swiping and explain empty swipe results.
    def test_provider_swipe_page_can_initiate_a_match(self):
        owner_app = self.app("jonas@student.unisg.ch")
        self.click(owner_app, "Like")
        self.assertEqual(database.get_matches_for_user(self.owner), [])
        seeker_app = self.app()
        self.click(seeker_app, "Like")
        self.assertEqual(len(database.get_matches_for_user(self.owner)), 1)

    def test_swipe_page_explains_gender_and_unknown_travel_exclusions(self):
        database.update_wg(self.wg, {"preferred_gender": "men only", "travel_time_min": None})
        app = self.app("jonas@student.unisg.ch")
        explanations = " ".join(caption.value for caption in app.caption)
        self.assertIn("travel time to HSG is unknown", explanations)
        self.assertIn("men only", explanations)
        self.assertIn("female", explanations)
        self.assertFalse(any(button.label == "Like" for button in app.button))

    def test_registration_page_logs_in_and_opens_profile(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
        app.switch_page("views/register.py").run()
        for widget, value in zip(app.text_input, ("New Student", "new.student@student.unisg.ch", "password123", "password123")):
            widget.input(value)
        self.click(app, "Create account")
        self.assertEqual(app.title[0].value, "My profile")
        self.assertIsNotNone(auth.login_user("new.student@student.unisg.ch", "password123"))

    def test_profile_criteria_role_switch_and_logout(self):
        app = self.app()
        app.switch_page("views/profile.py").run()
        app.text_input[0].input("Ana Updated")
        app.slider[0].set_value(0)
        self.click(app, "Save profile")
        self.assertEqual(database.get_user_by_id(self.seeker)["name"], "Ana Updated")
        self.assertEqual(database.get_user_by_id(self.seeker)["tidiness"], 0)
        app.switch_page("views/search_criteria.py").run()
        app.number_input[0].set_value(900)
        self.click(app, "Save criteria")
        self.assertEqual(app.title[0].value, "Find your WG")
        self.assertEqual(database.get_search_criteria(self.seeker)["max_rent"], 900)
        app.switch_page("views/profile.py").run()
        self.click(app, "Switch to “I offer a WG”")
        self.assertEqual(database.get_user_by_id(self.seeker)["role"], "offer_wg")
        self.click(app, "Log out")
        self.assertEqual(app.title[0].value, "🏠 WG Match")
        self.assertIsNone(app.session_state["user_id"])

    def test_listing_edits_update_the_existing_row(self):
        app = self.app("jonas@student.unisg.ch")
        app.switch_page("views/wg_listing.py").run()
        self.no_errors(app)
        next(widget for widget in app.text_input if widget.label == "Title").input("Updated room")
        with patch.object(transport_api, "get_travel_time_minutes") as api:
            self.click(app, "Save WG")
            api.assert_not_called()
        self.assertEqual(database.get_wg(self.wg)["title"], "Updated room")
        with contextlib.closing(database.get_connection()) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM wgs").fetchone()[0], 1)

    # AI-generated: OpenAI Codex, 19.11.2026. Prompt: make a feature where we can offer a WG.
    def test_seeker_can_start_offering_and_publish_a_wg(self):
        app = self.app()
        app.switch_page("views/wg_listing.py").run()
        self.no_errors(app)
        self.assertEqual(app.title[0].value, "Offer a WG")
        self.assertEqual(database.get_user_by_id(self.seeker)["role"], "search_wg")
        self.click(app, "Start offering a WG")
        self.assertEqual(database.get_user_by_id(self.seeker)["role"], "offer_wg")
        self.assertEqual(database.get_search_criteria(self.seeker), {"user_id": self.seeker, **self.criteria})

        # Invalid submissions keep the form open and do not create a listing.
        with patch.object(transport_api, "get_travel_time_minutes") as api:
            self.click(app, "Offer WG")
            api.assert_not_called()
        self.assertIsNone(database.get_wg_for_user(self.seeker))
        self.assertEqual(app.error[0].value, "Enter a title and street address.")

        next(widget for widget in app.text_input if widget.label == "Title").input(" My offered room ")
        next(widget for widget in app.text_input if widget.label == "Street and number").input("Teststrasse 33")
        next(widget for widget in app.checkbox if widget.label == "Simulate address verification (course demo)").check()
        with patch.object(transport_api, "get_travel_time_minutes", return_value=10), patch.object(transport_api, "get_location_coordinates", return_value=(47.42, 9.37)):
            self.click(app, "Offer WG")
        wg = database.get_wg_for_user(self.seeker)
        self.assertEqual(wg["title"], "My offered room")
        self.assertIn(wg["wg_id"], [row["wg_id"] for row in database.get_all_active_wgs()])
        self.assertEqual(database.get_wg_members(wg["wg_id"])[0]["is_main_tenant"], 1)
        self.assertEqual(app.title[0].value, "My WG")

        # The offer survives a fresh login, and can be hidden without deleting it.
        app = self.app()
        app.switch_page("views/wg_listing.py").run()
        self.assertEqual(next(widget for widget in app.text_input if widget.label == "Title").value, "My offered room")
        next(widget for widget in app.checkbox if widget.label == "Room available").uncheck()
        self.click(app, "Save WG")
        self.assertNotIn(wg["wg_id"], [row["wg_id"] for row in database.get_all_active_wgs()])

    def test_offer_can_be_saved_when_transport_is_unavailable(self):
        auth.register_user("new.owner@student.unisg.ch", "password123", "password123", "Owner", "offer_wg")
        app = self.app("new.owner@student.unisg.ch")
        app.switch_page("views/wg_listing.py").run()
        next(widget for widget in app.text_input if widget.label == "Title").input("Draft room")
        next(widget for widget in app.text_input if widget.label == "Street and number").input("Teststrasse 44")
        with patch.object(transport_api, "get_travel_time_minutes", return_value=None), patch.object(transport_api, "get_location_coordinates", return_value=None):
            self.click(app, "Offer WG")
        owner = database.get_user_by_email("new.owner@student.unisg.ch")
        wg = database.get_wg_for_user(owner["user_id"])
        self.assertIsNone(wg["travel_time_min"])
        self.assertEqual(wg["is_verified"], 0)
        self.assertNotIn(wg["wg_id"], [row["wg_id"] for row in database.get_all_active_wgs()])
        self.assertTrue(any("hidden from seekers" in notice.value for notice in app.info))

    def test_new_listing_fetches_and_saves_transport_data(self):
        auth.register_user("new.owner@student.unisg.ch", "password123", "password123", "Owner", "offer_wg")
        app = self.app("new.owner@student.unisg.ch")
        app.switch_page("views/wg_listing.py").run()
        next(widget for widget in app.text_input if widget.label == "Title").input("New room")
        next(widget for widget in app.text_input if widget.label == "Street and number").input("Teststrasse 22")
        next(widget for widget in app.checkbox if widget.label == "Simulate address verification (course demo)").check()
        with patch.object(transport_api, "get_travel_time_minutes", return_value=12) as api, patch.object(transport_api, "get_location_coordinates", return_value=(47.42, 9.37)):
            self.click(app, "Offer WG")
            api.assert_called_once()
        owner = database.get_user_by_email("new.owner@student.unisg.ch")
        wg = database.get_wg_for_user(owner["user_id"])
        self.assertEqual(wg["travel_time_min"], 12)
        self.assertEqual(wg["latitude"], 47.42)
        self.assertEqual(wg["is_verified"], 1)

    def test_swipe_match_chat_viewing_offer_and_accept(self):
        seeker_app = self.app()
        self.click(seeker_app, "Like")
        owner_app = self.app("jonas@student.unisg.ch")
        self.click(owner_app, "Like")
        self.assertEqual(len(database.get_matches_for_user(self.seeker)), 1)
        owner_app.switch_page("views/matches.py").run()
        self.click(owner_app, "Viewing done")
        self.click(owner_app, "Offer room")
        seeker_app.switch_page("views/matches.py").run()
        self.no_errors(seeker_app)
        seeker_app.chat_input[0].set_value("Hi, thanks for showing me the room!").run()
        self.no_errors(seeker_app)
        self.click(seeker_app, "Accept room")
        self.assertEqual(database.get_wg(self.wg)["is_active"], 0)
        self.assertEqual(database.get_matches_for_user(self.seeker)[0]["status"], "accepted")
        self.assertEqual(len(database.get_messages(database.get_matches_for_user(self.seeker)[0]["match_id"])), 1)

    def test_insights_charts_and_model_training(self):
        from data import seed_data
        with contextlib.redirect_stdout(io.StringIO()):
            seed_data.main()
        app = self.app("ana.demo@student.unisg.ch", "demo1234")
        app.switch_page("views/insights.py").run()
        self.no_errors(app)
        # Market charts: the map and the rent-vs-travel scatter.
        self.assertGreaterEqual(len(app.get("plotly_chart")), 2)
        self.click(app, "Train / refresh model")
        self.assertGreater(ml_model.get_model_metrics()["sample_rows"], 0)


if __name__ == "__main__":
    unittest.main()
