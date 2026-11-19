"""
===============================================================================
FILE:     app.py   (ENTRY POINT – start the app with:  streamlit run app.py)
OWNER:    Person A – Routing & Accounts   (only this person edits app.py!)
-------------------------------------------------------------------------------
PURPOSE
    The "front door" of the app. It does exactly four things:
      1. configures the browser tab (title, icon, layout)
      2. makes sure the SQLite database and its tables exist
      3. sets the default values in st.session_state (who is logged in?)
      4. decides WHICH pages appear in the menu (routing) and runs the page

WHAT BELONGS HERE
    - st.set_page_config, init_db(), session-state defaults, st.Page / st.navigation

WHAT DOES NOT BELONG HERE
    - page content (-> views/), business logic (-> core/), charts (-> components/)

ROUTING LOGIC
    not logged in            -> Log in, Register
    logged in as "search_wg" -> Swipe, Matches, Insights | Profile, Search criteria
    logged in as "offer_wg"  -> Swipe, Matches, Insights | Profile, My WG

STATUS:   DONE (step 4) (works). Add new pages here when the group agrees.
AI NOTE:  Generated with Claude (Anthropic), 15.11.2026 – see docs/ai_usage.md
===============================================================================
"""

import streamlit as st

from components.layout import sidebar_user_box
from core import database
from core.config import APP_NAME
from core.database import init_db

# --- 1. Browser tab settings (must be the first Streamlit command) -----------
st.set_page_config(page_title=APP_NAME, page_icon="🏠", layout="wide")

# --- 2. Create database file + tables if they don't exist yet ---------------
init_db()

# --- 3. Session state = the app's short-term memory while a user is online ---
#     user_id   -> id of the logged-in user (None = nobody logged in)
#     role      -> "search_wg" (looking for a room) or "offer_wg" (has a room)
#     user_name -> shown in the sidebar
#     wg_id     -> only for providers: the WG they manage
SESSION_DEFAULTS = {"user_id": None, "role": None, "user_name": None, "wg_id": None}
for key, value in SESSION_DEFAULTS.items():
    st.session_state.setdefault(key, value)

# AI-generated: OpenAI Codex, 19.11.2026. Keep account state in sync on reruns.
if st.session_state.user_id is not None:
    account = database.get_user_by_id(st.session_state.user_id)
    if account is None:
        for key in list(st.session_state):
            del st.session_state[key]
        st.session_state.update(SESSION_DEFAULTS)
    else:
        st.session_state.role = account["role"]
        st.session_state.user_name = account.get("name") or account["email"]

# --- 4. Define every page once (file path, menu title, icon) -----------------
login_page = st.Page("views/login.py", title="Log in", icon=":material/login:")
register_page = st.Page("views/register.py", title="Register", icon=":material/person_add:")
profile_page = st.Page("views/profile.py", title="My profile", icon=":material/person:")
criteria_page = st.Page("views/search_criteria.py", title="Search criteria", icon=":material/tune:")
listing_page = st.Page("views/wg_listing.py", title="My WG", icon=":material/home:")
swipe_page = st.Page("views/swipe.py", title="Swipe", icon=":material/swipe:")
matches_page = st.Page("views/matches.py", title="Matches & chat", icon=":material/favorite:")
insights_page = st.Page("views/insights.py", title="Insights", icon=":material/insights:")

# --- 5. Build the menu depending on login status and role -------------------
if st.session_state.user_id is None:
    navigation = st.navigation([login_page, register_page])
elif st.session_state.role == "search_wg":
    navigation = st.navigation(
        {
            "Find a WG": [swipe_page, matches_page, insights_page],
            "My account": [profile_page, criteria_page],
        }
    )
else:  # role == "offer_wg"
    navigation = st.navigation(
        {
            "Find a flatmate": [swipe_page, matches_page, insights_page],
            "My account": [profile_page, listing_page],
        }
    )

# Sidebar box with name, role and logout button (only when logged in)
if st.session_state.user_id is not None:
    sidebar_user_box()

# --- 6. Run the page the user selected ---------------------------------------
# AI-generated: OpenAI Codex, 19.11.2026. Navigate after authentication/role changes.
destination = st.session_state.pop("_next_page", None)
if destination:
    st.switch_page(destination)
navigation.run()
