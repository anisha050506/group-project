"""Log in with a saved HSG account."""
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: code everything missing.
import streamlit as st
from components.layout import log_in_session
from core import auth
from core.config import APP_NAME

st.title(f"🏠 {APP_NAME}")
st.write("Find flatmates who fit your lifestyle — for HSG students in St. Gallen.")
with st.form("login_form"):
    email = st.text_input("HSG email", placeholder="firstname.lastname@student.unisg.ch")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Log in", type="primary")
if submitted:
    user = auth.login_user(email, password)
    if user:
        log_in_session(user)
    else:
        st.error("Email or password is wrong.")
st.page_link("views/register.py", label="No account yet? Register here", icon=":material/person_add:")
st.caption("Course demo: student and address verification are simulated.")
