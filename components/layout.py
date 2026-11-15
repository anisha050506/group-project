"""
===============================================================================
FILE:     components/layout.py
OWNER:    Person A – Routing & Accounts
-------------------------------------------------------------------------------
PURPOSE
    Small helpers every page uses:
      require_login()      -> stop the page if nobody is logged in
      require_role(role)   -> stop the page if the user has the wrong role
      log_in_session(user) -> write the logged-in user into st.session_state
      logout()             -> clear the session and go back to the login page
      sidebar_user_box()   -> name, role and logout button in the sidebar
      todo_box(...)        -> the yellow "under construction" box on unfinished
                              pages (delete the call once your page is built)

STATUS:   DONE (step 4).
AI NOTE:  Generated with Claude (Anthropic), 15.11.2026 – see docs/ai_usage.md
===============================================================================
"""

import streamlit as st

from core.config import ROLES

SESSION_KEYS = ["user_id", "role", "user_name", "wg_id"]


def require_login() -> None:
    """Call at the top of every page that needs a logged-in user."""
    if st.session_state.get("user_id") is None:
        st.warning("Please log in first.")
        st.stop()


def require_role(role: str) -> None:
    """Call at the top of pages that only seekers or only providers may see."""
    require_login()
    if st.session_state.get("role") != role:
        st.info(f"This page is only for users who chose “{ROLES[role]}”.")
        st.stop()


def log_in_session(user: dict) -> None:
    """Store the logged-in user (dict from the database) and reload the app."""
    st.session_state.user_id = user["user_id"]
    st.session_state.role = user["role"]
    st.session_state.user_name = user.get("name") or user.get("email")
    st.rerun()  # app.py rebuilds the menu for the new role


def logout() -> None:
    """Forget the user and reload -> app.py shows the login page again."""
    for key in SESSION_KEYS:
        st.session_state[key] = None
    st.rerun()


def sidebar_user_box() -> None:
    """Name, role and logout button at the bottom of the sidebar."""
    with st.sidebar:
        st.divider()
        st.markdown(f"**{st.session_state.user_name or 'User'}**")
        st.caption(ROLES.get(st.session_state.role, ""))
        if st.button("Log out", icon=":material/logout:", width="stretch"):
            logout()


def todo_box(owner: str, goal: str, todos: list[str], uses: list[str] | None = None) -> None:
    """Shows what still has to be built on a placeholder page."""
    with st.container(border=True):
        st.markdown(f"🚧 **Under construction** · Owner: **{owner}**")
        st.write(goal)
        st.markdown("\n".join(f"- [ ] {item}" for item in todos))
        if uses:
            st.caption("Uses: " + " · ".join(f"`{name}`" for name in uses))
