"""
===============================================================================
FILE:     core/config.py
OWNER:    Person B – Data   (change only after agreeing with the group!)
-------------------------------------------------------------------------------
PURPOSE
    ONE place for every name and choice list that several files share.
    IMPORT from here instead of typing strings, e.g.
        from core.config import SLIDERS, GENDERS
    -> change something here once, and the whole app follows.

WHAT DOES NOT BELONG HERE
    - functions, database queries, Streamlit code

AI NOTE:  Generated with Claude (Anthropic), 15.11.2026 – see docs/ai_usage.md
===============================================================================
"""

# =============================================================================
# General (normally no need to change)
# =============================================================================
APP_NAME = "WG Match"
CITY = "St. Gallen"
UNIVERSITY_ADDRESS = "Dufourstrasse 50, 9000 St. Gallen"  # main HSG campus
ALLOWED_EMAIL_DOMAIN = "@student.unisg.ch"                # only HSG students

# File paths (relative to the repository root)
DB_PATH = "data/wg_match.db"           # created automatically, NOT on GitHub
MODEL_PATH = "models/match_model.pkl"  # trained ML model

# Roles: key stored in the database -> text shown to the user
ROLES = {
    "search_wg": "I look for a WG",
    "offer_wg": "I offer a WG",
}


# =============================================================================
# ✏️ 1  BEHAVIOURAL SLIDERS (scale 0–10)
# -----------------------------------------------------------------------------
# Seekers AND WG members answer the same questions, so they can be compared.

#   After adding / removing / renaming a key: delete data/wg_match.db (or run
#   the seed script again). The profile page, the database table and the
#   match score adapt automatically – no other file needs editing.
#
# FORMAT
#   "key": {"label": "shown above the slider",
#           "low":   "meaning of 0",
#           "high":  "meaning of 10"},
# =============================================================================
SLIDER_MIN = 0
SLIDER_MAX = 10

SLIDERS = {
    "tidiness":          {"label": "Tidiness",          "low": "Mess does not bother me",        "high": "Everything must always be tidy"},
    "sociability":       {"label": "Sociability",       "low": "I prefer to keep to myself",     "high": "I want to do a lot with my flatmates"},
    "noise_tolerance":   {"label": "Noise tolerance",   "low": "I need a lot of quiet",          "high": "Noise does not bother me"},
    "guests":            {"label": "Guests",            "low": "Almost never have guests",       "high": "Very often guests / parties"},
    "sleep_rhythm":      {"label": "Sleep rhythm",      "low": "Early bird",                     "high": "Night owl"},
    "cooking_together":  {"label": "Cooking together",  "low": "Everyone cooks for themselves",  "high": "We often cook together"},
    "cleaning_schedule": {"label": "Cleaning schedule", "low": "Relaxed, as needed",             "high": "Fixed cleaning schedule"},
    "time_at_home":      {"label": "Time at home",      "low": "Rarely at home",                 "high": "Very often at home"},
}

# Automatically built from SLIDERS – do not edit by hand
SLIDER_KEYS = list(SLIDERS.keys())

# How important each slider is for the match score (1.0 = normal, 2.0 = double).
# Default: all equal. To weight one slider differently, e.g.:
#     MATCH_WEIGHTS["tidiness"] = 2.0
MATCH_WEIGHTS = {key: 1.0 for key in SLIDER_KEYS}


# =============================================================================
# ✏️ 2  PROFILE CHOICE LISTS
# -----------------------------------------------------------------------------
# HOW TO CHANGE: add / remove / rename entries inside the [ ].
# The dropdowns on the profile and search pages update automatically.
# =============================================================================
GENDERS = ["female", "male", "diverse", "prefer not to say"]
FLATMATE_GENDER_PREFS = ["any", "women only", "men only"]
LANGUAGES = ["DE", "EN", "FR", "IT", "ES", "PT", "other"]
DEGREES = ["BWL", "VWL", "IA", "Law", "CS", "Other"]
STUDY_LEVELS = ["Assessment", "Bachelor", "Master", "PhD", "Exchange"]


# =============================================================================
# ✏️ 3  WG CHOICE LISTS
# -----------------------------------------------------------------------------
# HOW TO CHANGE: add / remove / rename entries inside the [ ].
# The WG listing form updates automatically.
# =============================================================================
DISTRICTS = [
    "Zentrum", "Rotmonten", "Rosenberg", "St. Georgen", "Riethüsli", "Lachen",
    "St. Fiden", "Neudorf", "Langgasse", "Heiligkreuz", "Bruggen", "Winkeln",
]
AMENITIES = ["Washing machine", "Dishwasher", "Wi-Fi", "Garden", "Elevator", "Bike storage", "Parking"]
WG_TYPES = ["Purpose-only WG", "Social WG"]
SMOKING_OPTIONS = ["No", "Balcony only", "Yes"]


# =============================================================================
# ✏️ 4  LIMITS FOR INPUT FIELDS
# =============================================================================
MAX_RENT_CHF = 2000          # highest value on the "max rent" input
MAX_TRAVEL_TIME_MIN = 60     # highest value on the "max travel time" slider
