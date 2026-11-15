"""
===============================================================================
FILE:     core/matching.py
OWNER:    Person D – Matching & ML
-------------------------------------------------------------------------------
PURPOSE
    The heart of the app: decides WHICH WGs a seeker sees and in WHICH order
    (and the other way round for WG providers).

    Two steps:
      1. HARD FILTERS  – yes/no rules. If one fails, the WG is not shown at all.
                         (budget, move-in date, travel time, gender, smoking)
      2. SOFT MATCHING – a compatibility score 0–100 % from the 8 sliders.
                         Later the ML model (ml_model.py) can improve this score.

WHAT BELONGS HERE
    - filter rules, score formula, ranking, "biggest mismatch" explanation
WHAT DOES NOT BELONG HERE
    - SQL (-> database.py), model training (-> ml_model.py), Streamlit code

INPUT FORMAT (dicts as returned by database.py)
    seeker   = {"user_id": 1, "tidiness": 7, "sociability": 4, ...}
    criteria = {"max_rent": 800, "move_in_date": "2027-02-01", "max_travel_time": 20,
                "preferred_flatmate_gender": "any", "smoker": 0}
    wg       = {"wg_id": 3, "rent_chf": 750, "available_from": "2027-01-15",
                "travel_time_min": 12, "smoking_allowed": "No", ...}
    wg_profile = {"tidiness": 6.5, "sociability": 5.0, ...}   (average of members)

STATUS:   Step 5 – all functions TODO. Start with compatibility_score().
AI NOTE:  Generated with Claude (Anthropic), 15.11.2026 – see docs/ai_usage.md
===============================================================================
"""

from core.config import MATCH_WEIGHTS, SLIDER_KEYS, SLIDER_MAX, SLIDERS


def passes_hard_filters(seeker: dict, criteria: dict, wg: dict) -> bool:
    """
    TODO: return True only if ALL rules are OK:
      - wg["rent_chf"]        <= criteria["max_rent"]
      - wg["available_from"]  <= criteria["move_in_date"]   (ISO strings compare fine)
      - wg["travel_time_min"] <= criteria["max_travel_time"]
      - gender: the WG's preferred_gender fits the seeker's gender, and the
        seeker's preferred_flatmate_gender fits the WG
      - smoking: smoker + wg["smoking_allowed"] == "No"  -> False
    """
    raise NotImplementedError("TODO (Person D): passes_hard_filters")


def compatibility_score(profile_a: dict, profile_b: dict) -> float:
    """
    TODO: similarity of two slider profiles, 0 (opposite) to 100 (identical).

    Suggested first formula (simple, explainable in the video):
        for each slider: difference = |a - b|           (0 ... 10)
        weighted average difference using MATCH_WEIGHTS
        score = 100 * (1 - average_difference / SLIDER_MAX)
    Round to 0 decimals.
    """
    raise NotImplementedError("TODO (Person D): compatibility_score")


def biggest_mismatches(profile_a: dict, profile_b: dict, top_n: int = 2) -> list[str]:
    """
    TODO: the top_n sliders with the largest difference, as readable text, e.g.
        ["Sleep rhythm: you 2, WG 8", "Guests: you 1, WG 7"]
    Use SLIDERS[key]["label"] for the name. Shown on the swipe card so the
    score is not a "black box".
    """
    raise NotImplementedError("TODO (Person D): biggest_mismatches")


def rank_wgs_for_seeker(seeker_id: int) -> list[dict]:
    """
    TODO: list of WGs for the swipe page, best first.
      1. load seeker, criteria, all active WGs, already-swiped WG ids (database.py)
      2. drop swiped WGs and WGs that fail passes_hard_filters
      3. for each WG: wg["score"] = compatibility_score(seeker, wg_profile)
         (later: blend with ml_model.predict_match_probability)
      4. sort by score, highest first, and return
    """
    raise NotImplementedError("TODO (Person D): rank_wgs_for_seeker")


def rank_seekers_for_wg(wg_id: int) -> list[dict]:
    """TODO: same idea for providers: seekers who liked this WG, sorted by score."""
    raise NotImplementedError("TODO (Person D): rank_seekers_for_wg")
