"""
===============================================================================
FILE:     views/matches.py        (page: "Matches & chat" – both roles)
OWNER:    Person E – Visualization, Matches & Video   (if 4 people: Person A)
-------------------------------------------------------------------------------
PURPOSE
    Everything after a mutual like, following the use cases:
      match -> chat -> viewing (logged with a button) -> room offered ->
      accepted -> (3 months later) feedback for the ML model

SUGGESTED LAYOUT
    left column : list of matches (database.get_matches_for_user)
    right column: selected match -> chat with st.chat_message / st.chat_input
                  (database.get_messages / database.send_message)
                  buttons: "Viewing done" | "Offer room" (provider) | "Accept" (seeker)
                  -> database.update_match(match_id, {...})
                  feedback form (satisfied yes/no) -> database.save_feedback

USES:     core/database.py, components/cards.py
AI NOTE:  Generated with Claude (Anthropic), 15.11.2026 – see docs/ai_usage.md
===============================================================================
"""

import streamlit as st

from components.layout import require_login, todo_box

require_login()
st.title("Matches & chat")

todo_box(
    owner="Person E – Visualization, Matches & Video",
    goal="List of mutual matches with a simple chat and the steps viewing → offer → accept.",
    todos=[
        "list matches (database.get_matches_for_user)",
        "chat with st.chat_message + st.chat_input",
        "“Viewing done” button (no real video call – mock)",
        "provider: “Offer room” · seeker: “Accept” → WG set inactive",
        "feedback form (satisfied yes/no) → database.save_feedback",
    ],
    uses=["database.get_matches_for_user", "database.get_messages", "database.send_message",
          "database.update_match", "database.save_feedback"],
)
