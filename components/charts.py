"""Plotly figures for lifestyle comparison and the local room market."""
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: code everything missing.
import pandas as pd
import plotly.graph_objects as go

from core.config import SLIDER_KEYS, SLIDERS, SLIDER_MIN, SLIDER_MAX


def radar_chart(profile_a: dict, profile_b: dict, name_a: str = "You", name_b: str = "WG"):
    labels = [SLIDERS[key]["label"] for key in SLIDER_KEYS]
    figure = go.Figure()
    for profile, name, color in ((profile_a, name_a, "#E67A2E"), (profile_b, name_b, "#C7902B")):
        values = [profile.get(key) for key in SLIDER_KEYS]
        figure.add_trace(go.Scatterpolar(r=values + values[:1], theta=labels + labels[:1], fill="toself", name=name, line_color=color))
    figure.update_layout(polar={"radialaxis": {"visible": True, "range": [SLIDER_MIN, SLIDER_MAX]}}, margin={"t": 35, "b": 35})
    return figure


def score_gauge(score: float):
    return go.Figure(go.Indicator(
        mode="gauge+number", value=max(0, min(100, score)), number={"suffix": "%"},
        title={"text": "Compatibility"},
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": "#E67A2E"}, "steps": [
            {"range": [0, 40], "color": "#F6E2D4"}, {"range": [40, 70], "color": "#FBEBD2"}, {"range": [70, 100], "color": "#EFE0C3"},
        ]},
    )).update_layout(height=280, margin={"t": 65, "b": 20})


def wg_map(wgs_df):
    figure = go.Figure()
    if not wgs_df.empty and {"latitude", "longitude"}.issubset(wgs_df.columns):
        points = wgs_df.copy()
        for key in ("latitude", "longitude"):
            points[key] = pd.to_numeric(points[key], errors="coerce")
        points = points.dropna(subset=["latitude", "longitude"])
        points = points[points.latitude.between(-90, 90) & points.longitude.between(-180, 180)]
        figure.add_trace(go.Scattermap(
            lat=points.latitude.tolist(), lon=points.longitude.tolist(), mode="markers",
            text=points.get("title", pd.Series("WG", index=points.index)).tolist(),
            marker={"size": 13, "color": "#E67A2E"}, hovertemplate="%{text}<extra></extra>",
        ))
    figure.update_layout(map={"style": "open-street-map", "center": {"lat": 47.4245, "lon": 9.3767}, "zoom": 11}, margin={"t": 0, "b": 0, "l": 0, "r": 0})
    return figure
