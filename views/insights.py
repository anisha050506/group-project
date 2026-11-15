"""
===============================================================================
FILE:     views/insights.py       (page: "Insights" – both roles)
OWNER:    Person E – Visualization, Matches & Video   (if 4 people: Person B)
-------------------------------------------------------------------------------
PURPOSE
    The data-visualization page (graded requirement no. 3) and the place to
    show the ML model's output (requirement no. 5) in the video.

IDEAS (pick 3–4)
    - radar chart: my profile vs. average of my matches
    - map of all WGs in St. Gallen, coloured by match score
    - average rent per district (bar chart) – is this listing fair?
    - travel time vs. rent (scatter)
    - ML output (to be defined later, e.g. "your lifestyle type")

USES:     core/database.py, core/ml_model.py, components/charts.py
AI NOTE:  Generated with Claude (Anthropic), 15.11.2026 – see docs/ai_usage.md
===============================================================================
"""

import streamlit as st

from components.layout import require_login, todo_box

require_login()
st.title("Insights")

todo_box(
    owner="Person E – Visualization, Matches & Video",
    goal="Charts that help users decide – and that look great in the 4-minute video.",
    todos=[
        "load all WGs into a pandas DataFrame",
        "map of WGs (charts.wg_map)",
        "average rent per district (charts.rent_by_district_chart)",
        "my profile vs. my matches (charts.radar_chart)",
        "ML result – to be defined later",
    ],
    uses=["database.get_all_active_wgs", "charts.*", "ml_model.* (later)"],
)
