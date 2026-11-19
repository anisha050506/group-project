"""Create a student account and continue to profile setup."""
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: code everything missing.
import streamlit as st
from components.layout import log_in_session
from core.auth import login_user, register_user
from core.config import ROLES

st.title("Create your account")
st.caption("Use your @student.unisg.ch email. Student verification is simulated in this course demo.")
with st.form("register_form"):
    name = st.text_input("First name", max_chars=80)
    email = st.text_input("HSG email", placeholder="firstname.lastname@student.unisg.ch")
    col1, col2 = st.columns(2)
    password = col1.text_input("Password", type="password")
    password_repeat = col2.text_input("Repeat password", type="password")
    role = st.radio("What do you want to do?", options=list(ROLES), format_func=ROLES.get, horizontal=True)
    submitted = st.form_submit_button("Create account", type="primary")
if submitted:
    success, message = register_user(email, password, password_repeat, name, role)
    if success:
        user = login_user(email, password)
        log_in_session(user, next_page="views/profile.py")
    else:
        st.error(message)
st.page_link("views/login.py", label="Already registered? Log in", icon=":material/login:")
