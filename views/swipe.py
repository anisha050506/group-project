"""
===============================================================================
FILE:     views/swipe.py          (page: "Swipe" – both roles)
OWNER:    Person D – Matching & ML
-------------------------------------------------------------------------------
PURPOSE
    The core experience. One card at a time, sorted by match score.
      Seeker   -> swipes through verified WGs        (matching.rank_wgs_for_seeker)
      Provider -> swipes through seekers who liked
                  their WG                           (matching.rank_seekers_for_wg)
    Like / pass is saved with database.save_swipe(); if both sides liked
    each other -> "It's a match! 🎉" and it appears under Matches & chat.

SUGGESTED FLOW
    candidates = matching.rank_wgs_for_seeker(st.session_state.user_id)
    i = st.session_state.setdefault("swipe_index", 0)
    if i >= len(candidates): st.info("No more WGs – check back later"); st.stop()
    card  -> components.cards.wg_card(candidates[i], score, mismatches)
    chart -> components.charts.radar_chart(my_profile, wg_profile)
    buttons ❌ Pass / ❤️ Like -> database.save_swipe(...) -> swipe_index += 1 -> st.rerun()

USES:     core/matching.py, core/database.py, components/cards.py, components/charts.py
AI NOTE:  Generated with Claude (Anthropic), 15.11.2026 – see docs/ai_usage.md
===============================================================================
"""

import streamlit as st

from components.layout import require_login, todo_box

require_login()
is_seeker = st.session_state.role == "search_wg"
st.title("Swipe – find your WG" if is_seeker else "Swipe – find your new flatmate")

todo_box(
    owner="Person D – Matching & ML",
    goal=(
        "Show one " + ("WG" if is_seeker else "seeker") +
        " at a time, best match first, with score, radar chart and Like / Pass buttons."
    ),
    todos=[
        "get ranked candidates from core/matching.py",
        "draw the current card with components/cards.py",
        "radar chart: you vs. candidate (components/charts.py)",
        "Like / Pass buttons → database.save_swipe() → next card",
        "show “It's a match! 🎉” when save_swipe() returns True",
        "empty state when no candidates are left",
    ],
    uses=["matching.rank_wgs_for_seeker", "matching.rank_seekers_for_wg", "database.save_swipe",
          "cards.wg_card", "cards.seeker_card", "charts.radar_chart"],
)
