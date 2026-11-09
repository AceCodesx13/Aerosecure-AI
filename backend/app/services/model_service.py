import os
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from ..schemas.prediction import PredictionRequest, PredictionResponse


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODEL_PATH = (
    PROJECT_ROOT / "artifacts" / "releases" / "v1" / "model.joblib"
)


@lru_cache
def load_model_bundle() -> dict:
    model_path = Path(
        os.getenv("AEROSECURE_MODEL_PATH", str(DEFAULT_MODEL_PATH))
    )

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model artifact was not found at: {model_path}"
        )

    # Only load model artifacts created by your trusted project code.
    bundle = joblib.load(model_path)

    required_items = {"pipeline", "margin", "features", "metadata"}
    missing_items = required_items.difference(bundle)

    if missing_items:
        raise ValueError(
            f"Model artifact is missing required items: {missing_items}"
        )

    return bundle


def predict_delivery(request: PredictionRequest) -> PredictionResponse:
    bundle = load_model_bundle()

    request_data = request.model_dump()
    model_input = pd.DataFrame([request_data])

    # Put the columns in the exact order expected by the trained pipeline.
    model_input = model_input[bundle["features"]]

    prediction = float(bundle["pipeline"].predict(model_input)[0])
    prediction = max(1.0, prediction)

    margin = float(bundle["margin"])
    conservative_prediction = prediction + margin

    return PredictionResponse(
        predicted_delivery_days=round(prediction, 3),
        conservative_delivery_days=round(
            conservative_prediction, 3
        ),
        model_source="scikit-learn-random-forest-v1",
    )