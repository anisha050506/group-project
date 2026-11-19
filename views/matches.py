"""Live inbox, conversations, viewings, room offers, and satisfaction feedback."""
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: make conversations async and organize chats like WhatsApp.
import re

import streamlit as st

from components import cards
from components.chat import (
    CHAT_STYLES, conversation_header_html, conversation_title,
    local_chat_datetime, message_history_html,
)
from components.layout import require_login
from core import database


def open_conversation(key: str, match_id: int) -> None:
    st.session_state[key] = match_id


def plain_label(value: str) -> str:
    """Keep names and message previews literal in Markdown button labels."""
    return re.sub(r"([\\`*_\[\]<>])", r"\\\1", value.replace("\n", " "))


def match_details(match: dict, user_id: int) -> None:
    """Keep the viewing and offer workflow available below the chat."""
    selected = match["match_id"]
    is_seeker = match["seeker_id"] == user_id
    members = database.get_wg_members(match["wg_id"])
    is_main = any(member["user_id"] == user_id and member["is_main_tenant"] for member in members)
    with st.expander("Room details & next steps"):
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
    if is_seeker and match["status"] == "accepted":
        with st.expander("How is living together?"):
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


@st.fragment(run_every="2s")
def live_inbox(user_id: int) -> None:
    # Re-query on every tick; a thread becoming available needs no page refresh.
    if st.session_state.get("user_id") != user_id:
        return
    require_login()
    conversations = database.get_conversations_for_user(user_id)
    if not conversations:
        st.info("A mutual like creates a conversation. Start with Swipe to meet a room or flatmate.")
        return
    by_id = {item["match_id"]: item for item in conversations}
    selection_key = f"active_chat_{user_id}"
    if st.session_state.get(selection_key) not in by_id:
        st.session_state[selection_key] = conversations[0]["match_id"]
    selected = st.session_state[selection_key]
    match = by_id[selected]
    messages = database.get_messages(selected)
    if messages and messages[-1]["message_id"] > match["last_read_message_id"]:
        database.mark_conversation_read(selected, user_id, messages[-1]["message_id"])
    match["unread_count"] = 0

    inbox_col, conversation_col = st.columns([1, 2.3], gap="medium")
    with inbox_col:
        st.subheader("Chats")
        query = st.text_input("Search conversations", placeholder="Name or WG", key=f"chat_search_{user_id}").strip().casefold()
        filtered = [item for item in conversations if query in f"{item['seeker_name']} {item['wg_title']}".casefold()]
        with st.container(height=480, border=False):
            if not filtered:
                st.caption("No conversations match your search.")
            for item in filtered:
                title = plain_label(conversation_title(item, user_id))
                badge = f" · {item['unread_count']} new" if item["unread_count"] else ""
                preview = item["last_message_text"] or "Say hello to your new match"
                if item["last_message_text"]:
                    prefix = "You" if item["last_sender_id"] == user_id else item["last_sender_name"] or "Flatmate"
                    preview = f"{prefix}: {preview}"
                preview = plain_label(preview[:75] + ("…" if len(preview) > 75 else ""))
                timestamp = local_chat_datetime(item["last_message_at"] or item["created_at"]).strftime("%d %b · %H:%M")
                st.button(
                    f"{title}{badge}\n\n{preview}", key=f"conversation_{user_id}_{item['match_id']}",
                    type="primary" if item["match_id"] == selected else "secondary", width="stretch",
                    on_click=open_conversation, args=(selection_key, item["match_id"]),
                    help=f"{timestamp} · {item['status']}",
                )

    with conversation_col:
        title = conversation_title(match, user_id)
        subtitle = f"{match['wg_title']} · {match['status'].capitalize()}" if match["seeker_id"] != user_id else f"WG conversation · {match['status'].capitalize()}"
        st.html(conversation_header_html(title, subtitle))
        with st.container(height=440, border=False, autoscroll=True, key=f"chat_history_{selected}"):
            st.html(message_history_html(messages, user_id))
        if text := st.chat_input("Write a message…", max_chars=4000, key=f"chat_{user_id}_{selected}"):
            try:
                database.send_message(selected, user_id, text)
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        st.caption("Live · New messages appear automatically. All times are local to St. Gallen.")
        match_details(match, user_id)


require_login()
st.title("Matches & chat")
st.html(CHAT_STYLES)
live_inbox(st.session_state.user_id)
