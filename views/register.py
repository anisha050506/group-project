"""
===============================================================================
FILE:     views/register.py       (page: "Register")
OWNER:    Person A – Routing & Accounts
-------------------------------------------------------------------------------
PURPOSE
    Create an account: HSG email, password, first name and role
    ("I look for a WG" / "I offer a WG"). The rest of the profile is filled
    in afterwards on "My profile".

TO DO
    [ ] call auth.register_user(...) on submit and show its message
    [ ] on success: log the user in directly (auth.login_user + log_in_session)
    [ ] after login, send the user to "My profile" (st.switch_page)

USES:     core/auth.py, core/config.py (ROLES), components/layout.py
AI NOTE:  Generated with Claude (Anthropic), 15.11.2026 – see docs/ai_usage.md
===============================================================================
"""

import streamlit as st

from core import auth
from core.config import ROLES

st.title("Create your account")
st.caption("Only verified HSG students can join (@student.unisg.ch).")

with st.form("register_form"):
    name = st.text_input("First name")
    email = st.text_input("HSG email", placeholder="firstname.lastname@student.unisg.ch")
    col1, col2 = st.columns(2)
    password = col1.text_input("Password", type="password")
    password_repeat = col2.text_input("Repeat password", type="password")
    role = st.radio("What do you want to do?", options=list(ROLES), format_func=ROLES.get, horizontal=True)
    submitted = st.form_submit_button("Create account", type="primary")

if submitted:
    try:
        success, message = auth.register_user(email, password, password_repeat, name, role)
        (st.success if success else st.error)(message)
    except NotImplementedError:
        st.info("Registration is not coded yet (core/auth.py → register_user).")

st.page_link("views/login.py", label="Already registered? Log in", icon=":material/login:")
