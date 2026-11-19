"""Edit a saved profile, lifestyle answers, photo, and account role."""
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: code everything missing.
from datetime import date
from pathlib import Path
import streamlit as st
from components.forms import option_index, number_value
from components.layout import require_login
from components.onboarding import getting_started
from core import database
from core.uploads import save_photo
from core.config import DEGREES, GENDERS, LANGUAGES, ROLES, SLIDER_MAX, SLIDER_MIN, SLIDERS, STUDY_LEVELS

require_login()
st.title("My profile")
user_id = st.session_state.user_id
user = database.get_user_by_id(user_id)
getting_started(user)
if user.get("photo_path") and Path(user["photo_path"]).is_file():
    st.image(user["photo_path"], width=180)
with st.form(f"profile_form_{user_id}"):
    st.subheader("About me")
    col1, col2 = st.columns(2)
    data = {"name": col1.text_input("First name", user.get("name") or "", max_chars=80)}
    data["birth_year"] = col2.number_input("Birth year", min_value=1900, max_value=date.today().year, value=int(number_value(user, "birth_year", 2004)))
    data["gender"] = col1.selectbox("Gender", GENDERS, index=option_index(GENDERS, user.get("gender")))
    data["languages"] = ",".join(col2.multiselect("Languages", LANGUAGES, default=[lang for lang in (user.get("languages") or "").split(",") if lang in LANGUAGES]))
    data["degree"] = col1.selectbox("Degree", DEGREES, index=option_index(DEGREES, user.get("degree")))
    data["study_level"] = col2.selectbox("Study level", STUDY_LEVELS, index=option_index(STUDY_LEVELS, user.get("study_level")))
    data["bio"] = st.text_area("Short bio", user.get("bio") or "", max_chars=2000)
    upload = st.file_uploader("Profile photo (up to 5 MB)", type=["jpg", "jpeg", "png", "webp"])
    remove_photo = st.checkbox("Remove current photo") if user.get("photo_path") else False
    st.subheader("How I live")
    st.caption("Be honest — these eight answers are what we match you on. Drag each slider between the two extremes.")
    for key, info in SLIDERS.items():
        data[key] = st.slider(
            info["label"], SLIDER_MIN, SLIDER_MAX, value=int(number_value(user, key, 5)),
            help=f"{SLIDER_MIN} = {info['low']}  ·  {SLIDER_MAX} = {info['high']}",
        )
        st.caption(f"⟵ {info['low']}　　{info['high']} ⟶")
    submitted = st.form_submit_button("Save profile", type="primary")
if submitted:
    try:
        if not data["name"].strip():
            raise ValueError("Enter your first name.")
        data["name"] = data["name"].strip()
        if upload:
            data["photo_path"] = save_photo(upload, f"user_{user_id}")
        elif remove_photo:
            data["photo_path"] = None
        database.update_profile(user_id, data)
        st.session_state.user_name = data["name"]
        st.session_state["_notice"] = "Profile saved."
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))
if st.session_state.role == "search_wg":
    st.page_link("views/search_criteria.py", label="Set your search criteria", icon=":material/tune:")
else:
    st.page_link("views/wg_listing.py", label="Create or edit your WG", icon=":material/home:")
st.divider()
st.subheader("My role")
other_role = "offer_wg" if st.session_state.role == "search_wg" else "search_wg"
st.write(f"Current role: {ROLES[st.session_state.role]}")
if st.button(f"Switch to “{ROLES[other_role]}”"):
    database.update_role(user_id, other_role)
    st.session_state.role = other_role
    st.session_state["_next_page"] = "views/profile.py"
    st.rerun()
