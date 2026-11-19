"""One candidate at a time, ranked by lifestyle and optional ML predictions."""
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: code everything missing.
import streamlit as st
from components import cards, charts
from components.layout import require_login
from core import database, matching

require_login()
is_seeker = st.session_state.role == "search_wg"
user_id = st.session_state.user_id
user = database.get_user_by_id(user_id)
st.title("Find your WG" if is_seeker else "Find your new flatmate")
if not matching.profile_is_complete(user):
    st.info("Complete your eight lifestyle sliders in My profile to start matching.")
    st.page_link("views/profile.py", label="Complete my profile")
    st.stop()
if is_seeker:
    if not database.get_search_criteria(user_id):
        st.info("Set your budget, move-in date, and travel limit first.")
        st.page_link("views/search_criteria.py", label="Set search criteria")
        st.stop()
    if any(match["status"] == "accepted" and match["seeker_id"] == user_id for match in database.get_matches_for_user(user_id)):
        st.success("You have accepted a room. Continue in Matches & chat.")
        st.stop()
    candidates = matching.rank_wgs_for_seeker(user_id)
else:
    wg = database.get_wg_for_user(user_id)
    if not wg:
        st.info("Create your WG listing first.")
        st.page_link("views/wg_listing.py", label="Create my WG")
        st.stop()
    if not wg["is_active"] or not wg["is_verified"]:
        st.info("Your WG needs an active listing and simulated address verification before swiping.")
        st.page_link("views/wg_listing.py", label="Manage my WG")
        st.stop()
    candidates = matching.rank_seekers_for_wg(wg["wg_id"])
if not candidates:
    # AI-generated: OpenAI Codex, 19.11.2026. Prompt: explain why Cyril cannot swipe on Jack's WG.
    st.info("No more rooms meet your criteria right now. Adjust your search or check back later." if is_seeker else "No unswiped seekers meet this WG's requirements right now.")
    exclusions = matching.swipe_exclusions(user_id)
    if exclusions:
        with st.expander("Why candidates are hidden", expanded=True):
            for item in exclusions:
                st.write(item["name"])
                for reason in item["reasons"]:
                    st.caption(reason)
        st.page_link("views/search_criteria.py" if is_seeker else "views/wg_listing.py", label="Edit search criteria" if is_seeker else "Edit WG requirements")
    st.stop()
# Saved swipes disappear from ranking, so always show the first remaining row.
candidate = candidates[0]
st.caption(f"{len(candidates)} candidate{'s' if len(candidates) != 1 else ''} remaining")
profile = candidate["wg_profile"]
left, right = st.columns([3, 2])
with left:
    if is_seeker:
        cards.wg_card(candidate, candidate["score"], matching.biggest_mismatches(user, profile))
    else:
        cards.seeker_card(candidate, candidate["score"], matching.biggest_mismatches(profile, candidate))
with right:
    st.plotly_chart(charts.radar_chart(user if is_seeker else profile, profile if is_seeker else candidate, "You" if is_seeker else "Your WG", "WG" if is_seeker else "Seeker"), width="stretch")
    if candidate["ml_probability"] is not None:
        st.caption(f"Lifestyle: {candidate['lifestyle_score']:.0f}% · Estimated satisfaction: {candidate['ml_probability']:.0%}. Ranking uses 80% lifestyle and 20% model prediction. The demo model uses synthetic feedback.")
    else:
        st.caption("Ranking uses the weighted average of your eight lifestyle differences. Train the model in Insights once enough feedback exists.")
pass_col, like_col = st.columns(2)
passed = pass_col.button("Pass", width="stretch")
liked = like_col.button("Like", type="primary", width="stretch")
if passed or liked:
    seeker_id = user_id if is_seeker else candidate["user_id"]
    wg_id = candidate["wg_id"] if is_seeker else wg["wg_id"]
    try:
        new_match = database.save_swipe(seeker_id, wg_id, "seeker" if is_seeker else "wg", liked)
        st.session_state["_notice"] = "It's a match! Open Matches & chat to say hello." if new_match else ("Like saved." if liked else "Passed.")
        st.rerun()
    except ValueError as exc:
        st.warning(str(exc))
