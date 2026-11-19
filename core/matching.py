"""Hard requirements, explainable lifestyle scores, and candidate ranking."""
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: code everything missing.
import math

from core import database, ml_model
from core.config import MATCH_WEIGHTS, SLIDER_KEYS, SLIDER_MIN, SLIDER_MAX, SLIDERS


def profile_is_complete(profile: dict) -> bool:
    """A score needs all eight lifestyle answers, including valid zero values."""
    return all(
        isinstance(profile.get(key), (int, float)) and math.isfinite(profile[key])
        and SLIDER_MIN <= profile[key] <= SLIDER_MAX for key in SLIDER_KEYS
    )


def passes_hard_filters(seeker: dict, criteria: dict, wg: dict) -> bool:
    """Unknown listing values cannot satisfy a corresponding explicit limit."""
    for listing_key, limit_key in (("rent_chf", "max_rent"), ("travel_time_min", "max_travel_time")):
        limit, value = criteria.get(limit_key), wg.get(listing_key)
        if limit is not None and (value is None or value > limit):
            return False
    move_in = criteria.get("move_in_date")
    if move_in:
        if not wg.get("available_from") or wg["available_from"] > move_in:
            return False
        if wg.get("available_until") and wg["available_until"] <= move_in:
            return False
    gender_rules = {"women only": "female", "men only": "male"}
    expected_gender = gender_rules.get(wg.get("preferred_gender"))
    if expected_gender and seeker.get("gender") != expected_gender:
        return False
    member_gender = gender_rules.get(criteria.get("preferred_flatmate_gender"))
    if member_gender:
        members = wg.get("members")
        if members is None:
            members = database.get_wg_members(wg["wg_id"]) if wg.get("wg_id") else []
        if not members or any(member.get("gender") != member_gender for member in members):
            return False
    if criteria.get("smoker") and wg.get("smoking_allowed") not in {"Yes", "Balcony only"}:
        return False
    return True


def compatibility_score(profile_a: dict, profile_b: dict) -> float:
    """Weighted similarity from 0 to 100, using shared answered sliders."""
    total, weight = 0.0, 0.0
    for key in SLIDER_KEYS:
        a, b = profile_a.get(key), profile_b.get(key)
        if a is not None and b is not None and math.isfinite(a) and math.isfinite(b):
            w = max(0, MATCH_WEIGHTS.get(key, 1.0))
            total += abs(a - b) * w
            weight += w
    if not weight:
        return 0.0
    return round(max(0.0, min(100.0, 100 * (1 - total / weight / (SLIDER_MAX - SLIDER_MIN)))), 0)


def biggest_mismatches(profile_a: dict, profile_b: dict, top_n: int = 2) -> list[str]:
    """Readable differences, with the first profile labelled 'you'."""
    shared = [key for key in SLIDER_KEYS if profile_a.get(key) is not None and profile_b.get(key) is not None]
    shared.sort(key=lambda key: abs(profile_a[key] - profile_b[key]), reverse=True)
    return [
        f"{SLIDERS[key]['label']}: you {profile_a[key]:g}, them {profile_b[key]:g}"
        for key in shared[:max(0, top_n)] if profile_a[key] != profile_b[key]
    ]


def _score_candidate(candidate: dict, seeker: dict, profile: dict, model) -> dict:
    score = compatibility_score(seeker, profile)
    candidate["lifestyle_score"] = score
    candidate["ml_probability"] = None
    if model is not None:
        probability = ml_model.predict_match_probability(seeker, profile, model=model)
        candidate["ml_probability"] = probability
        score = round(0.8 * score + 0.2 * probability * 100)
    candidate["score"] = score
    candidate["wg_profile"] = profile
    return candidate


def _available_model():
    try:
        return ml_model.load_model()
    except (ValueError, OSError):
        return None  # New installations can rank by lifestyle without feedback.


def rank_wgs_for_seeker(seeker_id: int) -> list[dict]:
    seeker = database.get_user_by_id(seeker_id)
    criteria = database.get_search_criteria(seeker_id)
    if not seeker or not seeker["is_verified"] or not criteria or not profile_is_complete(seeker):
        return []
    if any(match["seeker_id"] == seeker_id and match["status"] == "accepted" for match in database.get_matches_for_user(seeker_id)):
        return []
    swiped = set(database.get_swiped_wg_ids(seeker_id))
    model, candidates = _available_model(), []
    for wg in database.get_all_active_wgs():
        if wg["wg_id"] in swiped:
            continue
        wg["members"] = database.get_wg_members(wg["wg_id"])
        if any(member["user_id"] == seeker_id for member in wg["members"]):
            continue
        if not passes_hard_filters(seeker, criteria, wg):
            continue
        profile = database.get_wg_lifestyle_profile(wg["wg_id"])
        if profile_is_complete(profile):
            candidates.append(_score_candidate(wg, seeker, profile, model))
    return sorted(candidates, key=lambda row: (-row["score"], row["wg_id"]))


def rank_seekers_for_wg(wg_id: int) -> list[dict]:
    wg = database.get_wg(wg_id)
    if not wg or not wg["is_active"] or not wg["is_verified"]:
        return []
    profile = database.get_wg_lifestyle_profile(wg_id)
    if not profile_is_complete(profile):
        return []
    wg["members"] = database.get_wg_members(wg_id)
    model, candidates = _available_model(), []
    for seeker in database.get_seekers_who_liked_wg(wg_id):
        criteria = database.get_search_criteria(seeker["user_id"])
        if any(match["seeker_id"] == seeker["user_id"] and match["status"] == "accepted" for match in database.get_matches_for_user(seeker["user_id"])):
            continue
        if criteria and seeker["is_verified"] and profile_is_complete(seeker) and passes_hard_filters(seeker, criteria, wg):
            candidates.append(_score_candidate(seeker, seeker, profile, model))
    return sorted(candidates, key=lambda row: (-row["score"], row["user_id"]))
