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


# AI-generated: OpenAI Codex, 19.11.2026. Prompt: diagnose why Cyril cannot swipe on Jack's WG.
def hard_filter_reasons(seeker: dict, criteria: dict, wg: dict) -> list[str]:
    """Explain unmet requirements, including unknown values for explicit limits."""
    reasons = []
    for listing_key, limit_key in (("rent_chf", "max_rent"), ("travel_time_min", "max_travel_time")):
        limit, value = criteria.get(limit_key), wg.get(listing_key)
        if limit is not None:
            if value is None:
                reasons.append("The WG's rent is unknown." if listing_key == "rent_chf" else f"The WG's travel time to HSG is unknown; the seeker's limit is {limit:g} minutes.")
            elif value > limit:
                reasons.append(f"Rent is CHF {value:g}; the seeker's limit is CHF {limit:g}." if listing_key == "rent_chf" else f"Travel time is {value:g} minutes; the seeker's limit is {limit:g} minutes.")
    move_in = criteria.get("move_in_date")
    if move_in:
        if not wg.get("available_from"):
            reasons.append("The WG's availability date is unknown.")
        elif wg["available_from"] > move_in:
            reasons.append(f"The room is available from {wg['available_from']}, after the requested move-in date {move_in}.")
        if wg.get("available_until") and wg["available_until"] <= move_in:
            reasons.append("The rental ends before or on the requested move-in date.")
    gender_rules = {"women only": "female", "men only": "male"}
    expected_gender = gender_rules.get(wg.get("preferred_gender"))
    if expected_gender and seeker.get("gender") != expected_gender:
        reasons.append(f"The WG allows {wg['preferred_gender']}; the seeker's gender is saved as {seeker.get('gender') or 'unspecified'}.")
    member_gender = gender_rules.get(criteria.get("preferred_flatmate_gender"))
    if member_gender:
        members = wg.get("members")
        if members is None:
            members = database.get_wg_members(wg["wg_id"]) if wg.get("wg_id") else []
        if not members or any(member.get("gender") != member_gender for member in members):
            reasons.append(f"The WG's members do not meet the seeker's flatmate preference ({criteria['preferred_flatmate_gender']}).")
    if criteria.get("smoker") and wg.get("smoking_allowed") not in {"Yes", "Balcony only"}:
        reasons.append("The seeker smokes, but the WG does not allow smoking.")
    return reasons


def passes_hard_filters(seeker: dict, criteria: dict, wg: dict) -> bool:
    """Unknown listing values cannot satisfy a corresponding explicit limit."""
    return not hard_filter_reasons(seeker, criteria, wg)


def compatibility_score(profile_a: dict, profile_b: dict, weights: dict | None = None) -> float:
    """Weighted similarity from 0 to 100, using shared answered sliders.

    `weights` sets how much each lifestyle factor counts; it defaults to the
    neutral MATCH_WEIGHTS (all equal). Ranking passes the weights the model
    learned from real matches so important factors count for more.
    """
    weights = weights or MATCH_WEIGHTS
    total, weight = 0.0, 0.0
    for key in SLIDER_KEYS:
        a, b = profile_a.get(key), profile_b.get(key)
        if a is not None and b is not None and math.isfinite(a) and math.isfinite(b):
            w = max(0, weights.get(key, 1.0))
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


def _score_candidate(candidate: dict, seeker: dict, profile: dict, model, weights: dict | None = None) -> dict:
    score = compatibility_score(seeker, profile, weights)
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
        return None  # New installations can rank by lifestyle without a trained model.


def rank_wgs_for_seeker(seeker_id: int) -> list[dict]:
    seeker = database.get_user_by_id(seeker_id)
    criteria = database.get_search_criteria(seeker_id)
    if not seeker or not seeker["is_verified"] or not criteria or not profile_is_complete(seeker):
        return []
    if any(match["seeker_id"] == seeker_id and match["status"] == "accepted" for match in database.get_matches_for_user(seeker_id)):
        return []
    swiped = set(database.get_swiped_wg_ids(seeker_id))
    model, weights, candidates = _available_model(), ml_model.get_learned_weights(), []
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
            candidates.append(_score_candidate(wg, seeker, profile, model, weights))
    return sorted(candidates, key=lambda row: (-row["score"], row["wg_id"]))


def rank_seekers_for_wg(wg_id: int) -> list[dict]:
    wg = database.get_wg(wg_id)
    if not wg or not wg["is_active"] or not wg["is_verified"]:
        return []
    profile = database.get_wg_lifestyle_profile(wg_id)
    if not profile_is_complete(profile):
        return []
    wg["members"] = database.get_wg_members(wg_id)
    member_ids = {member["user_id"] for member in wg["members"]}
    swiped = set(database.get_swiped_seeker_ids(wg_id))
    model, weights, candidates = _available_model(), ml_model.get_learned_weights(), []
    # Either side can initiate; only this WG's own votes remove a seeker here.
    for seeker in database.get_all_seekers():
        if seeker["user_id"] in swiped or seeker["user_id"] in member_ids:
            continue
        criteria = database.get_search_criteria(seeker["user_id"])
        if any(match["seeker_id"] == seeker["user_id"] and match["status"] == "accepted" for match in database.get_matches_for_user(seeker["user_id"])):
            continue
        if criteria and seeker["is_verified"] and profile_is_complete(seeker) and passes_hard_filters(seeker, criteria, wg):
            candidates.append(_score_candidate(seeker, seeker, profile, model, weights))
    return sorted(candidates, key=lambda row: (-row["score"], row["user_id"]))


def swipe_exclusions(user_id: int) -> list[dict]:
    """Explain hidden pairs using the same requirements as candidate ranking."""
    user = database.get_user_by_id(user_id)
    if not user:
        return []
    is_seeker = user["role"] == "search_wg"
    wg = None if is_seeker else database.get_wg_for_user(user_id)
    if not is_seeker and not wg:
        return []
    rows = database.get_all_active_wgs() if is_seeker else database.get_all_seekers()
    swiped = set(database.get_swiped_wg_ids(user_id) if is_seeker else database.get_swiped_seeker_ids(wg["wg_id"]))
    exclusions = []
    for row in rows:
        seeker, listing = (user, row) if is_seeker else (row, wg)
        criteria = database.get_search_criteria(seeker["user_id"])
        members = database.get_wg_members(listing["wg_id"])
        reasons = []
        if not seeker["is_verified"]:
            reasons.append("The seeker has not completed simulated student verification.")
        if not profile_is_complete(seeker):
            reasons.append("The seeker needs to complete all eight lifestyle sliders in My profile.")
        if not criteria:
            reasons.append("The seeker has not saved search criteria.")
        else:
            reasons.extend(hard_filter_reasons(seeker, criteria, {**listing, "members": members}))
        if any(member["user_id"] == seeker["user_id"] for member in members):
            reasons.append("The seeker already belongs to this WG.")
        if not profile_is_complete(database.get_wg_lifestyle_profile(listing["wg_id"])):
            reasons.append("The WG's members need to complete their lifestyle sliders.")
        if not listing["is_active"]:
            reasons.append("The room is marked unavailable.")
        if not listing["is_verified"]:
            reasons.append("The listing needs simulated address verification.")
        if any(match["seeker_id"] == seeker["user_id"] and match["status"] == "accepted" for match in database.get_matches_for_user(seeker["user_id"])):
            reasons.append("The seeker has already accepted a room.")
        if (listing["wg_id"] if is_seeker else seeker["user_id"]) in swiped:
            reasons.append("You have already liked or passed this candidate.")
        if reasons:
            exclusions.append({"name": listing["title"] if is_seeker else seeker["name"], "reasons": reasons})
    return exclusions
