"""Market charts, lifestyle comparisons, and transparent model evaluation."""
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: code everything missing.
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from components import charts
from components.layout import require_login
from core import database, matching, ml_model
from core.config import BRAND, SLIDER_KEYS

require_login()
st.title("Insights")
user_id = st.session_state.user_id
user = database.get_user_by_id(user_id)
wgs = database.get_all_active_wgs()
frame = pd.DataFrame(wgs)
count_col, rent_col, travel_col = st.columns(3)
count_col.metric("Available verified rooms", len(wgs))
if not frame.empty:
    average_rent = frame.rent_chf.mean()
    average_travel = frame.travel_time_min.mean()
    rent_col.metric("Average monthly rent", f"CHF {average_rent:,.0f}" if pd.notna(average_rent) else "Unknown")
    travel_col.metric("Average time to HSG", f"{average_travel:.0f} min" if pd.notna(average_travel) else "Unknown")
    st.subheader("Rooms around St. Gallen")
    st.plotly_chart(charts.wg_map(frame), width="stretch")
    mapped = frame[["latitude", "longitude"]].notna().all(axis=1).sum()
    st.caption(f"{mapped} of {len(frame)} rooms have map coordinates. Verification is simulated for the course demo.")
    st.subheader("Rent and travel time")
    points = frame.dropna(subset=["rent_chf", "travel_time_min"])
    figure = go.Figure(go.Scatter(
        x=points.travel_time_min.tolist(), y=points.rent_chf.tolist(), text=points.title.tolist(),
        mode="markers", marker={"size": 12, "color": BRAND["accent"]},
        hovertemplate="%{text}<br>%{x} min · CHF %{y}<extra></extra>",
    ))
    figure.update_layout(xaxis_title="Minutes to HSG", yaxis_title="Monthly rent (CHF)")
    st.plotly_chart(figure, width="stretch")
else:
    st.info("Market charts will appear when there are active, verified room listings.")

st.subheader("Your lifestyle and your matches")
match_rows = database.get_matches_for_user(user_id)
profiles = []
for match in match_rows:
    if match["status"] == "declined":
        continue
    if match["seeker_id"] == user_id:
        profiles.append(database.get_wg_lifestyle_profile(match["wg_id"]))
    else:
        profiles.append(database.get_user_by_id(match["seeker_id"]))
if profiles:
    average = pd.DataFrame(profiles).reindex(columns=SLIDER_KEYS).mean().to_dict()
    average = {key: value if pd.notna(value) else None for key, value in average.items()}
    own_wg = database.get_wg_for_user(user_id) if user["role"] == "offer_wg" else None
    own_profile = database.get_wg_lifestyle_profile(own_wg["wg_id"]) if own_wg else user
    left, right = st.columns([2, 1])
    left.plotly_chart(charts.radar_chart(own_profile, average, "Your WG" if own_wg else "You", "Average match"), width="stretch")
    right.plotly_chart(charts.score_gauge(matching.compatibility_score(own_profile, average)), width="stretch")
else:
    st.info("Your first mutual match will unlock this comparison.")

st.subheader("How the prediction model performs")
st.write("A random forest learns from the eight lifestyle differences and satisfaction feedback. Evaluation holds out entire seekers, then the final model is trained on all available feedback.")
st.caption("The supplied demo feedback is synthetic. These metrics describe the demo dataset and do not establish performance with real tenants.")
if st.button("Train / refresh model", type="primary"):
    try:
        with st.spinner("Training and evaluating…"):
            ml_model.train_model()
        st.success("Model trained and saved.")
    except (ValueError, OSError) as exc:
        st.warning(str(exc))
try:
    metrics = ml_model.get_model_metrics()
    accuracy_col, baseline_col, auc_col = st.columns(3)
    accuracy_col.metric("Held-out accuracy", f"{metrics['accuracy']:.1%}")
    baseline_col.metric("Majority baseline", f"{metrics['baseline_accuracy']:.1%}")
    auc_col.metric("ROC AUC", f"{metrics['roc_auc']:.3f}")
    st.caption(f"{metrics['training_rows']} training rows · {metrics['test_rows']} evaluation rows from {metrics['held_out_seekers']} held-out seekers · Trained {metrics['trained_at']}")
    st.write(f"Balanced accuracy: {metrics['balanced_accuracy']:.1%}. Brier score: {metrics['brier_score']:.3f} (lower is better).")
    st.caption("When available, candidate ranking combines 80% lifestyle compatibility with 20% estimated satisfaction. Refresh the model after collecting more feedback.")
except (ValueError, OSError) as exc:
    st.info(str(exc))
