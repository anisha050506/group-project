"""Save the seeker's hard requirements."""
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: code everything missing.
import streamlit as st
from components.forms import date_value, number_value, option_index
from components.layout import require_role
from core import database
from core.config import FLATMATE_GENDER_PREFS, MAX_RENT_CHF, MAX_TRAVEL_TIME_MIN

require_role("search_wg")
st.title("Search criteria")
st.caption("Rooms with unknown rent, availability, or travel time cannot meet a corresponding limit.")
criteria = database.get_search_criteria(st.session_state.user_id) or {}
with st.form("search_criteria_form"):
    col1, col2 = st.columns(2)
    data = {
        "max_rent": col1.number_input("Max. rent per month (CHF, incl. utilities)", 0, MAX_RENT_CHF, int(number_value(criteria, "max_rent", 800)), step=50),
        "move_in_date": col2.date_input("Move-in date", date_value(criteria.get("move_in_date"))).isoformat(),
        "max_travel_time": col1.slider("Max. travel time to HSG (minutes, public transport)", 0, MAX_TRAVEL_TIME_MIN, int(number_value(criteria, "max_travel_time", 20))),
        "preferred_flatmate_gender": col2.selectbox("Flatmates", FLATMATE_GENDER_PREFS, index=option_index(FLATMATE_GENDER_PREFS, criteria.get("preferred_flatmate_gender"))),
        "smoker": int(st.toggle("I smoke", value=bool(criteria.get("smoker")))),
    }
    submitted = st.form_submit_button("Save criteria", type="primary")
if submitted:
    database.save_search_criteria(st.session_state.user_id, data)
    st.session_state["_notice"] = "Search criteria saved."
    st.switch_page("views/swipe.py")
