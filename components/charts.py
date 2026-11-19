"""Plotly figures for lifestyle comparison and the local room market."""
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: code everything missing.
import pandas as pd
import plotly.graph_objects as go

from core.config import SLIDER_KEYS, SLIDERS, SLIDER_MIN, SLIDER_MAX


def radar_chart(profile_a: dict, profile_b: dict, name_a: str = "You", name_b: str = "WG"):
    labels = [SLIDERS[key]["label"] for key in SLIDER_KEYS]
    figure = go.Figure()
    for profile, name, color in ((profile_a, name_a, "#4c6ef5"), (profile_b, name_b, "#12b886")):
        values = [profile.get(key) for key in SLIDER_KEYS]
        figure.add_trace(go.Scatterpolar(r=values + values[:1], theta=labels + labels[:1], fill="toself", name=name, line_color=color))
    figure.update_layout(polar={"radialaxis": {"visible": True, "range": [SLIDER_MIN, SLIDER_MAX]}}, margin={"t": 35, "b": 35})
    return figure


def score_gauge(score: float):
    return go.Figure(go.Indicator(
        mode="gauge+number", value=max(0, min(100, score)), number={"suffix": "%"},
        title={"text": "Compatibility"},
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": "#4c6ef5"}, "steps": [
            {"range": [0, 40], "color": "#fff0f0"}, {"range": [40, 70], "color": "#fff8db"}, {"range": [70, 100], "color": "#e6fcf5"},
        ]},
    )).update_layout(height=280, margin={"t": 65, "b": 20})


def rent_by_district_chart(wgs_df):
    figure = go.Figure()
    if not wgs_df.empty and {"district", "rent_chf"}.issubset(wgs_df.columns):
        averages = wgs_df.groupby("district")["rent_chf"].mean().dropna().sort_values()
        figure.add_trace(go.Bar(x=averages.index.tolist(), y=averages.tolist(), marker_color="#4c6ef5"))
    figure.update_layout(xaxis_title="District", yaxis_title="Average monthly rent (CHF)", margin={"t": 20})
    return figure


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
            marker={"size": 13, "color": "#4c6ef5"}, hovertemplate="%{text}<extra></extra>",
        ))
    figure.update_layout(map={"style": "open-street-map", "center": {"lat": 47.4245, "lon": 9.3767}, "zoom": 11}, margin={"t": 0, "b": 0, "l": 0, "r": 0})
    return figure
