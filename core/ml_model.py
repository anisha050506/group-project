"""Random forest estimating satisfaction from eight lifestyle differences.

Evaluation holds out whole seekers so repeated feedback from a seeker never
appears on both sides of the evaluation split. Demo feedback is synthetic.
"""
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: code everything missing.
import json
import os
import pickle
import tempfile
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
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
    return make_pipeline(
        SimpleImputer(strategy="constant", fill_value=0.5),
        RandomForestClassifier(n_estimators=150, min_samples_leaf=5, random_state=42, class_weight="balanced", n_jobs=1),
    )


def train_model() -> dict:
    """Evaluate on held-out seekers, refit on all feedback, save locally."""
    data = database.get_training_data()
    data = data[data["satisfied"].isin([0, 1])]
    if len(data) < 20 or data["satisfied"].nunique() < 2 or data["seeker_id"].nunique() < 5:
        raise ValueError("Training needs at least 20 feedback rows, both outcomes, and 5 different seekers.")
    features = np.array([
        build_features(
            {key: row[f"seeker_{key}"] for key in SLIDER_KEYS},
            {key: row[f"wg_{key}"] for key in SLIDER_KEYS},
        ) for _, row in data.iterrows()
    ])
    labels = data["satisfied"].to_numpy(dtype=int)
    splitter = GroupShuffleSplit(n_splits=30, test_size=0.2, random_state=42)
    split = next(((a, b) for a, b in splitter.split(features, labels, data["seeker_id"])
                  if len(set(labels[a])) == 2 and len(set(labels[b])) == 2), None)
    if split is None:
        raise ValueError("More feedback from different seekers is needed for a balanced evaluation split.")
    train_ids, test_ids = split
    evaluation_model = _new_model().fit(features[train_ids], labels[train_ids])
    predictions = evaluation_model.predict(features[test_ids])
    probability = evaluation_model.predict_proba(features[test_ids])[:, list(evaluation_model.classes_).index(1)]
    metrics = {
        "accuracy": float(accuracy_score(labels[test_ids], predictions)),
        "balanced_accuracy": float(balanced_accuracy_score(labels[test_ids], predictions)),
        "roc_auc": float(roc_auc_score(labels[test_ids], probability)),
        "brier_score": float(brier_score_loss(labels[test_ids], probability)),
        "baseline_accuracy": float(accuracy_score(labels[test_ids], np.full(len(test_ids), int(np.mean(labels[train_ids]) >= 0.5)))),
        "training_rows": int(len(train_ids)), "test_rows": int(len(test_ids)),
        "feedback_rows": int(len(data)), "held_out_seekers": int(data.iloc[test_ids]["seeker_id"].nunique()),
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    bundle = {
        "version": 1, "slider_keys": SLIDER_KEYS, "database": str(Path(database.DB_PATH).resolve()),
        "model": _new_model().fit(features, labels), "metrics": metrics,
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
    """Load a saved model, training first if enough feedback is available."""
    return _load_bundle()["model"]


def get_model_metrics() -> dict:
    return _load_bundle()["metrics"]


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
