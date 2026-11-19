"""Conversations, viewings, room offers, acceptance, and satisfaction feedback."""
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: code everything missing.
import streamlit as st
from components import cards
from components.layout import require_login
from core import database

require_login()
st.title("Matches & chat")
user_id = st.session_state.user_id
matches = database.get_matches_for_user(user_id)
if not matches:
    st.info("A mutual like creates a match. Start with Swipe to meet a room or flatmate.")
    st.stop()
by_id = {match["match_id"]: match for match in matches}
selected = st.selectbox(
    "Choose a match", list(by_id),
    format_func=lambda match_id: f"{by_id[match_id]['wg_title'] if by_id[match_id]['seeker_id'] == user_id else by_id[match_id]['seeker_name']} · {by_id[match_id]['status']}",
    key=f"match_selection_{user_id}",
)
match = by_id[selected]
is_seeker = match["seeker_id"] == user_id
members = database.get_wg_members(match["wg_id"])
is_main = any(member["user_id"] == user_id and member["is_main_tenant"] for member in members)
with st.expander("Room and student details"):
    if is_seeker:
        cards.wg_card(database.get_wg(match["wg_id"]))
    else:
        cards.seeker_card(database.get_user_by_id(match["seeker_id"]))
st.caption(f"Status: {match['status']} · Viewing: {'done' if match['viewing_done'] else 'not recorded'}")
view_col, offer_col, decline_col = st.columns(3)
try:
    if not is_seeker and match["status"] == "open" and not match["viewing_done"] and view_col.button("Viewing done"):
        database.mark_viewing_done(selected, user_id)
        st.rerun()
    if is_main and match["status"] == "open" and match["viewing_done"] and offer_col.button("Offer room", type="primary"):
        database.change_match_status(selected, user_id, "offered")
        st.session_state["_notice"] = "Room offered. The seeker can now accept or decline."
        st.rerun()
    if is_seeker and match["status"] == "offered" and offer_col.button("Accept room", type="primary"):
        database.change_match_status(selected, user_id, "accepted")
        st.session_state["_notice"] = "Room accepted! The listing is now inactive."
        st.rerun()
    if (is_seeker or is_main) and match["status"] in {"open", "offered"} and decline_col.button("Decline match"):
        database.change_match_status(selected, user_id, "declined")
        st.rerun()
except ValueError as exc:
    st.error(str(exc))

st.subheader("Conversation")
for message in database.get_messages(selected):
    with st.chat_message("user" if message["sender_id"] == user_id else "assistant"):
        st.caption(f"{message['sender_name']} · {message['created_at']}")
        st.write(message["text"])
if text := st.chat_input("Write a message", max_chars=4000, key=f"chat_{selected}"):
    try:
        database.send_message(selected, user_id, text)
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))
if st.button("Refresh conversation"):
    st.rerun()
if is_seeker and match["status"] == "accepted":
    st.subheader("How is living together?")
    st.caption("After living together, share feedback to help improve matching.")
    if database.has_match_feedback(user_id, match["wg_id"]):
        st.success("Thank you. Your feedback has been recorded.")
    else:
        with st.form(f"feedback_{selected}"):
            satisfied = st.radio("Are you happy with this match?", [True, False], format_func=lambda value: "Yes" if value else "No")
            comment = st.text_area("Comment (optional)", max_chars=2000)
            submit = st.form_submit_button("Save feedback")
        if submit:
            try:
                database.save_match_feedback(selected, user_id, satisfied, comment)
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
