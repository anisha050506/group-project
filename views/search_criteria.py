"""
===============================================================================
FILE:     views/search_criteria.py   (page: "Search criteria" – seekers only)
OWNER:    Person C – Profiles, Listings & API
-------------------------------------------------------------------------------
PURPOSE
    The seeker's HARD criteria. They are used by matching.passes_hard_filters()
    to hide WGs that can never work (too expensive, too far, wrong date ...).

TO DO
    [ ] pre-fill with saved values (database.get_search_criteria)
    [ ] save -> database.save_search_criteria(user_id, data)
    [ ] after saving: st.switch_page("views/swipe.py")

USES:     core/config.py, core/database.py, components/layout.py
AI NOTE:  Generated with Claude (Anthropic), 15.11.2026 – see docs/ai_usage.md
===============================================================================
"""

import datetime

import streamlit as st

from components.layout import require_role
from core import database
from core.config import FLATMATE_GENDER_PREFS, MAX_RENT_CHF, MAX_TRAVEL_TIME_MIN

require_role("search_wg")
st.title("Search criteria")
st.caption("WGs that don't meet these criteria are never shown to you.")

data = {}
col1, col2 = st.columns(2)
data["max_rent"] = col1.number_input("Max. rent per month (CHF, incl. utilities)", 300, MAX_RENT_CHF, 800, step=50)
data["move_in_date"] = col2.date_input("Move-in date", datetime.date.today()).isoformat()
data["max_travel_time"] = col1.slider("Max. travel time to HSG (minutes, public transport)", 5, MAX_TRAVEL_TIME_MIN, 20)
data["preferred_flatmate_gender"] = col2.selectbox("Flatmates", FLATMATE_GENDER_PREFS)
data["smoker"] = int(st.toggle("I smoke"))

if st.button("Save criteria", type="primary"):
    try:
        database.save_search_criteria(st.session_state.user_id, data)
        st.success("Saved! Go to Swipe to see your matches.")
    except NotImplementedError:
        st.info("Saving is not coded yet (core/database.py → save_search_criteria).")
        st.json(data)
