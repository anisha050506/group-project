"""
===============================================================================
FILE:     views/wg_listing.py     (page: "My WG" – providers only)
OWNER:    Person C – Profiles, Listings & API
-------------------------------------------------------------------------------
PURPOSE
    A provider creates / edits the listing of their WG and the free room.
    On save, the travel time to HSG is fetched ONCE from the transport API
    and stored with the WG.

TO DO
    [ ] load existing WG (database.get_wg_for_user) and pre-fill the form
    [ ] on save: travel = transport_api.get_travel_time_minutes(address)
    [ ] new WG -> database.create_wg(data, user_id); else database.update_wg(...)
    [ ] store the wg_id in st.session_state.wg_id
    [ ] show WG lifestyle profile (database.get_wg_lifestyle_profile) as radar chart
    [ ] verification status: mock "Verified ✅ / Pending ⏳" (no real postcard)

USES:     core/config.py, core/database.py, core/transport_api.py, components/charts.py
AI NOTE:  Generated with Claude (Anthropic), 15.11.2026 – see docs/ai_usage.md
===============================================================================
"""

import datetime

import streamlit as st

from components.layout import require_role
from core import database, transport_api
from core.config import AMENITIES, DISTRICTS, FLATMATE_GENDER_PREFS, SMOKING_OPTIONS, WG_TYPES

require_role("offer_wg")
st.title("My WG")

data = {}
with st.form("wg_form"):
    st.subheader("Location")
    data["title"] = st.text_input("Title", placeholder="Sunny room in Rotmonten, 5 min to HSG")
    col1, col2 = st.columns(2)
    data["address"] = col1.text_input("Street and number")
    data["district"] = col2.selectbox("District", DISTRICTS)

    st.subheader("Costs")
    col1, col2, col3 = st.columns(3)
    data["rent_chf"] = col1.number_input("Rent / month incl. utilities (CHF)", 0, 3000, 750, step=10)
    data["utilities_chf"] = col2.number_input("of which utilities (CHF)", 0, 500, 80, step=10)
    data["deposit_chf"] = col3.number_input("Deposit (CHF)", 0, 6000, 1500, step=100)

    st.subheader("Room & flat")
    col1, col2, col3 = st.columns(3)
    data["room_size_m2"] = col1.number_input("Room size (m²)", 5, 50, 14)
    data["flat_size_m2"] = col2.number_input("Flat size (m²)", 20, 300, 90)
    data["num_flatmates"] = col3.number_input("Flatmates (without new person)", 1, 10, 2)
    data["furnished"] = int(col1.checkbox("Furnished"))
    data["private_bathroom"] = int(col2.checkbox("Private bathroom"))
    data["balcony"] = int(col3.checkbox("Balcony"))
    data["amenities"] = ",".join(st.multiselect("Amenities", AMENITIES))

    st.subheader("Availability")
    col1, col2 = st.columns(2)
    data["available_from"] = col1.date_input("Available from", datetime.date.today()).isoformat()
    data["min_rental_months"] = col2.number_input("Minimum rental period (months)", 0, 24, 6)

    st.subheader("House rules")
    col1, col2 = st.columns(2)
    data["wg_type"] = col1.selectbox("WG type", WG_TYPES)
    data["smoking_allowed"] = col2.selectbox("Smoking", SMOKING_OPTIONS)
    data["preferred_gender"] = col1.selectbox("New flatmate", FLATMATE_GENDER_PREFS)
    data["pets_allowed"] = int(col2.checkbox("Pets allowed"))

    st.subheader("Description")
    data["description"] = st.text_area("Tell seekers about your WG")
    # TODO: photos -> st.file_uploader("Photos", accept_multiple_files=True)

    submitted = st.form_submit_button("Save WG", type="primary")

if submitted:
    try:
        data["travel_time_min"] = transport_api.get_travel_time_minutes(f"{data['address']}, St. Gallen")
        st.session_state.wg_id = database.create_wg(data, st.session_state.user_id)
        st.success("WG saved!")
    except NotImplementedError as error:
        st.info(f"Not coded yet: {error}")
        st.json(data)
