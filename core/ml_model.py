"""Logistic regression estimating the chance a match succeeds (both sides
accept) from the eight lifestyle differences, and the per-factor weights it
learns. Evaluation uses repeated held-out-seeker cross-validation so repeated
matches from a seeker never appear on both sides of a split. Demo outcomes are
synthetic.
"""
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: code everything missing.
# AI-generated: Claude (Anthropic), 22.11.2026. Prompt: "predict mutual matches
# with logistic regression and expose learned per-factor weights".
import json
import os
import pickle
import tempfile
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline

from core import database
from core.config import MODEL_PATH, SLIDER_KEYS, SLIDER_MIN, SLIDER_MAX


def build_features(seeker: dict, wg_profile: dict) -> list[float]:
    """Differences scaled to 0–1; missing answers are NaN for imputation."""
    return [
        abs(seeker[key] - wg_profile[key]) / (SLIDER_MAX - SLIDER_MIN)
        if seeker.get(key) is not None and wg_profile.get(key) is not None else float("nan")
        for key in SLIDER_KEYS
    ]


def _new_model():
    # Logistic regression: one coefficient per lifestyle factor, so the model is
    # interpretable and its learned weights can feed the compatibility score.
    return make_pipeline(
        SimpleImputer(strategy="constant", fill_value=0.5),
        LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
    )


def learned_weights_from(model) -> dict:
    """Turn the logistic-regression coefficients into one positive importance
    per lifestyle factor, normalised so the average weight is 1.0 (the neutral
    all-equal baseline). A bigger weight means a gap in that factor matters more.
    """
    coefficients = model.named_steps["logisticregression"].coef_[0]
    importance = np.abs(coefficients)
    average = importance.mean() or 1.0
    return {key: float(importance[i] / average) for i, key in enumerate(SLIDER_KEYS)}


def train_model() -> dict:
    """Evaluate on held-out seekers, refit on all resolved matches, save locally."""
    data = database.get_training_data()
    data = data[data["matched"].isin([0, 1])]
    if len(data) < 20 or data["matched"].nunique() < 2 or data["seeker_id"].nunique() < 5:
        raise ValueError("Training needs at least 20 resolved matches, both outcomes, and 5 different seekers.")
    features = np.array([
        build_features(
            {key: row[f"seeker_{key}"] for key in SLIDER_KEYS},
            {key: row[f"wg_{key}"] for key in SLIDER_KEYS},
        ) for _, row in data.iterrows()
    ])
    labels = data["matched"].to_numpy(dtype=int)
    # Repeated held-out-seeker cross-validation: average the scores over many
    # splits so the reported numbers are stable, not an accident of one split.
    splitter = GroupShuffleSplit(n_splits=25, test_size=0.2, random_state=42)
    folds = []
    for train_ids, test_ids in splitter.split(features, labels, data["seeker_id"]):
        if len(set(labels[train_ids])) < 2 or len(set(labels[test_ids])) < 2:
            continue
        model = _new_model().fit(features[train_ids], labels[train_ids])
        predictions = model.predict(features[test_ids])
        probability = model.predict_proba(features[test_ids])[:, list(model.classes_).index(1)]
        baseline = int(np.mean(labels[train_ids]) >= 0.5)
        folds.append({
            "accuracy": accuracy_score(labels[test_ids], predictions),
            "balanced_accuracy": balanced_accuracy_score(labels[test_ids], predictions),
            "roc_auc": roc_auc_score(labels[test_ids], probability),
            "brier_score": brier_score_loss(labels[test_ids], probability),
            "baseline_accuracy": accuracy_score(labels[test_ids], np.full(len(test_ids), baseline)),
            "test_rows": len(test_ids),
            "held_out_seekers": data.iloc[test_ids]["seeker_id"].nunique(),
        })
    if not folds:
        raise ValueError("More matches from different seekers are needed for a balanced evaluation.")
    mean = lambda key: float(np.mean([fold[key] for fold in folds]))
    metrics = {
        "accuracy": mean("accuracy"), "balanced_accuracy": mean("balanced_accuracy"),
        "roc_auc": mean("roc_auc"), "brier_score": mean("brier_score"),
        "baseline_accuracy": mean("baseline_accuracy"),
        "training_rows": int(len(labels) - mean("test_rows")), "test_rows": int(round(mean("test_rows"))),
        "sample_rows": int(len(data)), "held_out_seekers": int(round(mean("held_out_seekers"))),
        "cv_folds": len(folds), "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    final_model = _new_model().fit(features, labels)
    bundle = {
        "version": 1, "slider_keys": SLIDER_KEYS, "database": str(Path(database.DB_PATH).resolve()),
        "model": final_model, "metrics": metrics,
        "weights": learned_weights_from(final_model),
    }
    target = Path(MODEL_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".tmp", delete=False) as handle:
            temporary_path = Path(handle.name)
            pickle.dump(bundle, handle)
        os.replace(temporary_path, target)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    _read_bundle.cache_clear()
    return metrics


@lru_cache(maxsize=4)
def _read_bundle(path: str, modified_ns: int):
    with open(path, "rb") as handle:
        return pickle.load(handle)


def _load_bundle():
    path = Path(MODEL_PATH)
    if not path.exists():
        train_model()
    try:
        bundle = _read_bundle(str(path.resolve()), path.stat().st_mtime_ns)
    except (pickle.UnpicklingError, EOFError, AttributeError, ImportError) as exc:
        raise ValueError("The saved model cannot be loaded. Retrain it in Insights.") from exc
    if (not isinstance(bundle, dict) or bundle.get("version") != 1
            or bundle.get("slider_keys") != SLIDER_KEYS
            or bundle.get("database") != str(Path(database.DB_PATH).resolve())):
        raise ValueError("The saved model belongs to a different database or slider setup. Retrain it in Insights.")
    return bundle


def load_model():
    """Load a saved model, training first if enough match outcomes are available."""
    return _load_bundle()["model"]


def get_model_metrics() -> dict:
    return _load_bundle()["metrics"]


def get_learned_weights() -> dict | None:
    """The per-factor weights the model learned, or None when no usable model
    exists yet (so ranking can fall back to equal weights)."""
    try:
        return _load_bundle().get("weights")
    except (ValueError, OSError):
        return None


def predict_match_probability(seeker: dict, wg_profile: dict, model=None) -> float:
    """Estimated satisfaction probability; this is not a guarantee."""
    model = load_model() if model is None else model
    return float(model.predict_proba([build_features(seeker, wg_profile)])[0, list(model.classes_).index(1)])


if __name__ == "__main__":
    database.init_db()
    try:
        print(json.dumps(train_model(), indent=2))
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
