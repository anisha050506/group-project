"""
===============================================================================
FILE:     core/auth.py
OWNER:    Person A – Routing & Accounts
-------------------------------------------------------------------------------
PURPOSE
    Registration and login logic (no Streamlit code – the forms live in
    views/login.py and views/register.py).

WHAT BELONGS HERE
    - email validation (only @student.unisg.ch)
    - password hashing / checking  (passwords are NEVER stored in plain text)
    - register_user() and login_user(), which use core/database.py
WHAT DOES NOT BELONG HERE
    - st.session_state, forms, buttons  (-> views/ and components/layout.py)

STATUS:   Registration and login implemented; email verification is simulated.
AI NOTE:  Generated with Claude (Anthropic), 15.11.2026 – see docs/ai_usage.md
===============================================================================
"""

import hashlib
import re
import secrets
import sqlite3

from core import database
from core.config import ALLOWED_EMAIL_DOMAIN, ROLES

MIN_PASSWORD_LENGTH = 8


# =============================================================================
# Helpers   (DONE)
# =============================================================================
def is_valid_hsg_email(email: str) -> bool:
    """True if the email ends with @student.unisg.ch (case-insensitive)."""
    return bool(re.fullmatch(r"[a-z0-9][a-z0-9._+\-]*" + re.escape(ALLOWED_EMAIL_DOMAIN), email.strip().lower()))


def hash_password(password: str) -> str:
    """
    Turn a password into a salted hash "salt$hash" (Python standard library,
    no extra package needed). Same password + different salt = different hash.
    """
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Check a typed password against the stored "salt$hash"."""
    try:
        salt, expected = stored_hash.split("$", 1)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
        return secrets.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError, AttributeError):
        return False


# =============================================================================
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: code everything missing.
# Main functions
# =============================================================================
def register_user(email: str, password: str, password_repeat: str, name: str, role: str) -> tuple[bool, str]:
    """Create a demo account, returning success and a message for the form."""
    email, name = email.strip().lower(), name.strip()
    if not is_valid_hsg_email(email):
        return False, "Please use your HSG email (@student.unisg.ch)."
    if password != password_repeat:
        return False, "Passwords do not match."
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Use at least {MIN_PASSWORD_LENGTH} characters for your password."
    if not name or len(name) > 80:
        return False, "Enter a first name of 1–80 characters."
    if role not in ROLES:
        return False, "Please choose a valid role."
    if database.get_user_by_email(email):
        return False, "An account with this email already exists."
    try:
        user_id = database.create_user(email, hash_password(password), role, name)
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."
    # Course demo: checking the email domain simulates student verification.
    database.update_profile(user_id, {"is_verified": 1})
    return True, "Account created. Complete your profile to start matching."


def login_user(email: str, password: str) -> dict | None:
    """Return the account on valid credentials, otherwise None."""
    user = database.get_user_by_email(email)
    return user if user and verify_password(password, user["password_hash"]) else None
