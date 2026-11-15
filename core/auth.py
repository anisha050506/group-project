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

STATUS:   Step 4 – helpers are DONE, register_user / login_user are TODO.
AI NOTE:  Generated with Claude (Anthropic), 15.11.2026 – see docs/ai_usage.md
===============================================================================
"""

import hashlib
import secrets

from core import database
from core.config import ALLOWED_EMAIL_DOMAIN, ROLES

MIN_PASSWORD_LENGTH = 8


# =============================================================================
# Helpers   (DONE)
# =============================================================================
def is_valid_hsg_email(email: str) -> bool:
    """True if the email ends with @student.unisg.ch (case-insensitive)."""
    return email.strip().lower().endswith(ALLOWED_EMAIL_DOMAIN)


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
    salt, expected = stored_hash.split("$", 1)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return secrets.compare_digest(digest.hex(), expected)


# =============================================================================
# Main functions   (TODO)
# =============================================================================
def register_user(email: str, password: str, password_repeat: str, name: str, role: str) -> tuple[bool, str]:
    """
    TODO: create a new account. Return (success, message_for_the_user).

    Steps:
      1. is_valid_hsg_email(email)?            else -> (False, "Please use your HSG email")
      2. password == password_repeat?          else -> (False, "Passwords do not match")
      3. len(password) >= MIN_PASSWORD_LENGTH? else -> (False, "...")
      4. role in ROLES?
      5. database.get_user_by_email(email) is None?  else -> "Account already exists"
      6. database.create_user(email, hash_password(password), role, name)
      7. return (True, "Account created")
    """
    raise NotImplementedError("TODO (Person A): register_user")


def login_user(email: str, password: str) -> dict | None:
    """
    TODO: return the user dict if email + password are correct, else None.

    Steps:
      1. user = database.get_user_by_email(email.strip().lower())
      2. if user and verify_password(password, user["password_hash"]): return user
      3. otherwise return None   (don't tell WHICH part was wrong – security)
    """
    raise NotImplementedError("TODO (Person A): login_user")
