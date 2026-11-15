"""
===============================================================================
FILE:     core/ml_model.py
OWNER:    Person D – Matching & ML
-------------------------------------------------------------------------------
PURPOSE
    Our OWN trained machine-learning model (graded requirement no. 5:
    "you train and use your own model").

    >>> The exact ML approach will be decided by the group and added to this
        file and to the README later. The function names below are only
        placeholders so other files already know what to call. <<<

WHAT BELONGS HERE
    - preparing features from the training data (database.get_training_data())
    - training, evaluating (accuracy etc.), saving and loading the model
    - predicting for new seeker/WG pairs
WHAT DOES NOT BELONG HERE
    - SQL, Streamlit code, the hand-made score formula (-> matching.py)

TRAINING DATA
    Real feedback won't exist before the deadline -> data/seed_data.py will
    generate realistic fake feedback so the model can be trained and demoed.
    The trained model is saved to MODEL_PATH (see config.py).

STATUS:   Step 5 – placeholder. To be defined later by the group.
AI NOTE:  Generated with Claude (Anthropic), 15.11.2026 – see docs/ai_usage.md
===============================================================================
"""

from core.config import MODEL_PATH, SLIDER_KEYS  # noqa: F401  (used once implemented)


def build_features(seeker: dict, wg_profile: dict) -> list[float]:
    """TODO: turn one seeker/WG pair into numbers the model can read."""
    raise NotImplementedError("TODO (Person D): build_features – ML approach to be defined")


def train_model() -> dict:
    """TODO: load training data, train, evaluate, save to MODEL_PATH. Return metrics."""
    raise NotImplementedError("TODO (Person D): train_model – ML approach to be defined")


def load_model():
    """TODO: load the saved model from MODEL_PATH (train it first if missing)."""
    raise NotImplementedError("TODO (Person D): load_model – ML approach to be defined")


def predict_match_probability(seeker: dict, wg_profile: dict) -> float:
    """TODO: probability 0–1 that this seeker will be happy in this WG."""
    raise NotImplementedError("TODO (Person D): predict_match_probability – ML approach to be defined")
