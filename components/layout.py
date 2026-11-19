"""Authentication, navigation, and shared session helpers."""
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: code everything missing.
import streamlit as st

from core import database
from core.config import ROLES


def require_login() -> None:
    user_id = st.session_state.get("user_id")
    if user_id is None or database.get_user_by_id(user_id) is None:
        st.warning("Please log in first.")
        st.stop()
    notice = st.session_state.pop("_notice", None)
    if notice:
        st.success(notice)


def require_role(role: str) -> None:
    require_login()
    if st.session_state.get("role") != role:
        st.info(f"This page is for users who chose “{ROLES[role]}”.")
        st.stop()


def log_in_session(user: dict, next_page: str | None = None) -> None:
    # Clear widgets and selected conversations left by a previous account.
    for key in list(st.session_state):
        del st.session_state[key]
    wg = database.get_wg_for_user(user["user_id"])
    st.session_state.update(user_id=user["user_id"], role=user["role"], user_name=user.get("name") or user["email"], wg_id=wg["wg_id"] if wg else None)
    if next_page:
        st.session_state["_next_page"] = next_page
    st.rerun()


def logout() -> None:
    for key in list(st.session_state):
        del st.session_state[key]
    st.rerun()


def show_notifications() -> None:
    """Sidebar bell: unread messages and brand-new matches, plus a toast the
    first time a new one appears during this session."""
    user_id = st.session_state.get("user_id")
    if not user_id:
        return
    counts = st.session_state.get("_notif") or database.get_notification_counts(user_id)

    # Toast only for events that arrived AFTER this session's first render, so we
    # don't pop a toast for the backlog the moment someone logs in.
    seen = st.session_state.get("_notify_seen")
    if seen is not None:
        if counts["new_matches"] > seen.get("new_matches", 0):
            st.toast("It's a match!", icon="❤️")
        if counts["unread_messages"] > seen.get("unread_messages", 0):
            st.toast("New message", icon="✉️")
    st.session_state["_notify_seen"] = {
        "new_matches": counts["new_matches"],
        "unread_messages": counts["unread_messages"],
    }

    parts = []
    if counts["new_matches"]:
        parts.append(f"{counts['new_matches']} new match" + ("es" if counts["new_matches"] != 1 else ""))
    if counts["unread_messages"]:
        parts.append(f"{counts['unread_messages']} unread message" + ("s" if counts["unread_messages"] != 1 else ""))
    if parts:
        st.info(":material/notifications_active: " + " · ".join(parts))
    else:
        st.caption(":material/notifications: No new notifications")


def sidebar_user_box() -> None:
    with st.sidebar:
        st.divider()
        st.write(st.session_state.user_name or "User")
        st.caption(ROLES.get(st.session_state.role, ""))
        show_notifications()
        if st.button("Log out", icon=":material/logout:", width="stretch"):
            logout()
