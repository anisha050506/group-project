"""
===============================================================================
FILE:     components/cards.py
OWNER:    Person D – Matching & ML
-------------------------------------------------------------------------------
PURPOSE
    The "cards" users swipe through. Keeping them here means the swipe page
    and the matches page show WGs / seekers in exactly the same style.

WHAT BELONGS HERE
    - functions that DRAW one WG or one seeker with Streamlit
WHAT DOES NOT BELONG HERE
    - loading data or computing scores (the page passes everything in)

STATUS:   Step 5 – TODO. Look at the demo design for the layout.
AI NOTE:  Generated with Claude (Anthropic), 15.11.2026 – see docs/ai_usage.md
===============================================================================
"""

import streamlit as st  # noqa: F401  (used once implemented)


def wg_card(wg: dict, score: float | None = None, mismatches: list[str] | None = None) -> None:
    """
    TODO: draw one WG inside st.container(border=True):
      - photo (st.image) or placeholder, title, district
      - rent CHF / room m² / travel time to HSG (st.metric in 3 columns)
      - match score as big number or progress bar, verified badge
      - "Watch out:" + mismatches (from matching.biggest_mismatches)
      - short description
    """
    raise NotImplementedError("TODO (Person D): wg_card")


def seeker_card(seeker: dict, score: float | None = None, mismatches: list[str] | None = None) -> None:
    """TODO: same for a seeker (shown to WG providers): name, age, degree, languages, bio, score."""
    raise NotImplementedError("TODO (Person D): seeker_card")
