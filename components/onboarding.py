"""Getting-started checklist shown to new users so they know the few steps
needed before they can match (complete profile, lifestyle answers, and either
search criteria or a published WG). Rendered on the profile page."""
import streamlit as st

from core import database, matching

_BASIC_FIELDS = ("name", "birth_year", "gender", "degree", "study_level")


def _steps(user: dict) -> list[tuple[str, bool, str]]:
    """Return (label, done, page_link) for each onboarding step, by role."""
    user_id = user["user_id"]
    steps = [
        ("Fill in your profile", all(user.get(field) for field in _BASIC_FIELDS), "views/profile.py"),
        ("Answer the 8 lifestyle sliders", matching.profile_is_complete(user), "views/profile.py"),
    ]
    if st.session_state.get("role") == "search_wg":
        steps.append(("Set your search criteria", database.get_search_criteria(user_id) is not None, "views/search_criteria.py"))
    else:
        wg = database.get_wg_for_user(user_id)
        steps.append(("Publish your WG listing", bool(wg and wg["is_active"] and wg["is_verified"]), "views/wg_listing.py"))
    return steps


def steps_complete(user: dict) -> bool:
    """True when every onboarding step is done."""
    return all(done for _, done, _ in _steps(user))


def getting_started(user: dict) -> None:
    """Render the checklist with a progress bar. Hidden once everything is done,
    so finished users don't keep seeing it on their profile."""
    steps = _steps(user)
    done = sum(1 for _, ok, _ in steps if ok)
    total = len(steps)
    if done == total:
        return
    with st.container(border=True):
        st.markdown("#### Getting started")
        st.progress(done / total, text=f"{done} of {total} steps complete")
        for label, ok, link in steps:
            if ok:
                st.markdown(f":green[:material/check_circle:] ~{label}~")
            else:
                st.page_link(link, label=label, icon=":material/radio_button_unchecked:")
