"""
===============================================================================
FILE:     views/login.py          (page: "Log in")
OWNER:    Person A – Routing & Accounts
-------------------------------------------------------------------------------
PURPOSE
    First page a visitor sees. Short welcome + login form.

TO DO
    [ ] call auth.login_user(email, password) on submit
    [ ] success -> layout.log_in_session(user)   |   fail -> st.error(...)
    [ ] welcome text / logo matching the demo design
    [ ] REMOVE the developer shortcut before submission (10.12.2026)

USES:     core/auth.py, components/layout.py
AI NOTE:  Generated with Claude (Anthropic), 15.11.2026 – see docs/ai_usage.md
===============================================================================
"""

import streamlit as st

from components.layout import log_in_session
from core import auth
from core.config import APP_NAME

st.title(f"🏠 {APP_NAME}")
st.write("Find flatmates who actually fit you – for HSG students in St. Gallen.")

# --- Login form -----------------------------------------------------------------
with st.form("login_form"):
    email = st.text_input("HSG email", placeholder="firstname.lastname@student.unisg.ch")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Log in", type="primary")

if submitted:
    try:
        user = auth.login_user(email, password)
        if user:
            log_in_session(user)
        else:
            st.error("Email or password is wrong.")
    except NotImplementedError:
        st.info("Login is not coded yet (core/auth.py). Use the developer shortcut below.")

st.page_link("views/register.py", label="No account yet? Register here", icon=":material/person_add:")

# --- DEVELOPER SHORTCUT – lets the team test all pages before login works -----
# !!! Delete this whole block before submission !!!
with st.expander("🛠️ Developer shortcut (remove before submission)"):
    col1, col2 = st.columns(2)
    if col1.button("Enter as WG seeker (Ana)", width="stretch"):
        log_in_session({"user_id": -1, "role": "search_wg", "name": "Ana (demo)"})
    if col2.button("Enter as WG provider (Jonas)", width="stretch"):
        log_in_session({"user_id": -2, "role": "offer_wg", "name": "Jonas (demo)"})
