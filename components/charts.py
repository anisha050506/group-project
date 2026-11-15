"""
===============================================================================
FILE:     components/charts.py
OWNER:    Person E – Visualization, Matches & Video   (if 4 people: Person B)
-------------------------------------------------------------------------------
PURPOSE
    All charts of the app (graded requirement no. 3: "visualizes data that
    serves the use case"). Every function RETURNS a Plotly figure; the page
    shows it with  st.plotly_chart(fig).

WHAT BELONGS HERE
    - chart functions that take data (dicts / DataFrames) and return a figure
WHAT DOES NOT BELONG HERE
    - loading data from the database (the page does that and passes it in)

STATUS:   Step 5 – TODO.
AI NOTE:  Generated with Claude (Anthropic), 15.11.2026 – see docs/ai_usage.md
===============================================================================
"""

import plotly.graph_objects as go  # noqa: F401  (used once implemented)

from core.config import SLIDER_KEYS, SLIDERS  # noqa: F401


def radar_chart(profile_a: dict, profile_b: dict, name_a: str = "You", name_b: str = "WG"):
    """
    TODO: two overlapping shapes on the 8 sliders (go.Scatterpolar, fill="toself").
    Labels: SLIDERS[key]["label"]. Range 0–10. The STAR chart of the video.
    """
    raise NotImplementedError("TODO (Person E): radar_chart")


def score_gauge(score: float):
    """TODO: semicircle gauge 0–100 % for the match score (go.Indicator, mode="gauge+number")."""
    raise NotImplementedError("TODO (Person E): score_gauge")


def rent_by_district_chart(wgs_df):
    """TODO: bar chart of average rent per district (pandas groupby + plotly bar)."""
    raise NotImplementedError("TODO (Person E): rent_by_district_chart")


def wg_map(wgs_df):
    """TODO: map of all WGs (latitude/longitude columns), e.g. plotly scatter_map or st.map."""
    raise NotImplementedError("TODO (Person E): wg_map")
