"""
===============================================================================
FILE:     views/profile.py        (page: "My profile")
OWNER:    Person C – Profiles, Listings & API
-------------------------------------------------------------------------------
PURPOSE
    Personal profile + the 8 behavioural sliders + role switch.
    Same page for seekers and providers (both need sliders: a WG's
    "personality" is the average of its members' sliders).

TO DO
    [ ] pre-fill all widgets with the saved values (database.get_user_by_id)
    [ ] save button -> database.update_profile(user_id, data)
    [ ] role switch -> database.update_role + update st.session_state.role + st.rerun()
    [ ] optional: photo upload (st.file_uploader) saved to assets/uploads/

USES:     core/config.py, core/database.py, components/layout.py
AI NOTE:  Generated with Claude (Anthropic), 15.11.2026 – see docs/ai_usage.md
===============================================================================
"""

import streamlit as st

from components.layout import require_login
from core import database
from core.config import DEGREES, GENDERS, LANGUAGES, ROLES, SLIDER_MAX, SLIDER_MIN, SLIDERS, STUDY_LEVELS

require_login()
st.title("My profile")

data = {}  # everything the user enters is collected here and saved at the end

# --- 1. Personal information ------------------------------------------------------
st.subheader("About me")
col1, col2 = st.columns(2)
data["name"] = col1.text_input("First name", value=st.session_state.user_name or "")
data["birth_year"] = col2.number_input("Birth year", min_value=1950, max_value=2010, value=2004)
data["gender"] = col1.selectbox("Gender", GENDERS)
data["languages"] = ",".join(col2.multiselect("Languages", LANGUAGES, default=["DE", "EN"]))
data["degree"] = col1.selectbox("Degree", DEGREES)
data["study_level"] = col2.selectbox("Study level", STUDY_LEVELS)
data["bio"] = st.text_area("Short bio (1–2 sentences)", max_chars=200)

# --- 2. Behavioural sliders – generated automatically from config.SLIDERS -------------
st.subheader("How I live")
st.caption("Be honest – this decides who you are matched with.")
for key, info in SLIDERS.items():
    data[key] = st.slider(info["label"], SLIDER_MIN, SLIDER_MAX, value=5, key=f"slider_{key}")
    st.caption(f"{SLIDER_MIN} = {info['low']}  ·  {SLIDER_MAX} = {info['high']}")

# --- 3. Save -------------------------------------------------------------------------
if st.button("Save profile", type="primary"):
    try:
        database.update_profile(st.session_state.user_id, data)
        st.success("Profile saved!")
    except NotImplementedError:
        st.info("Saving is not coded yet (core/database.py → update_profile).")
        st.json(data)  # shows what WOULD be saved – handy for testing

# --- 4. Role switch --------------------------------------------------------------------
st.divider()
st.subheader("My role")
other_role = "offer_wg" if st.session_state.role == "search_wg" else "search_wg"
st.write(f"Current role: **{ROLES[st.session_state.role]}**")
if st.button(f"Switch to “{ROLES[other_role]}”"):
    # TODO (Person C): also call database.update_role(st.session_state.user_id, other_role)
    st.session_state.role = other_role
    st.rerun()
