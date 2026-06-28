from __future__ import annotations

from functools import lru_cache

import joblib
import numpy as np
import pandas as pd

from config import PREDICTION_MODEL_PATH
from schemas.prediction import PredictionRequest


NUMERIC_FEATURES = [
    "distance_km",
    "origin_lat",
    "origin_lon",
    "destination_lat",
    "destination_lon",
    "duration_hours",
    "departure_hour",
    "departure_month",
    "departure_dayofweek",
]
CATEGORICAL_FEATURES = ["operator_name", "service_type", "train_type", "country", "source_origin"]


class PredictionModelUnavailable(RuntimeError):
    pass


def _build_features(payload: PredictionRequest) -> pd.DataFrame:
    row = payload.model_dump()
    data = pd.DataFrame([row])

    for column in ["departure_time", "arrival_time"]:
        data[column] = pd.to_datetime(data[column], errors="coerce")

    duration = (data["arrival_time"] - data["departure_time"]).dt.total_seconds() / 3600
    data["duration_hours"] = duration.where(duration >= 0, duration + 24)
    data["departure_hour"] = data["departure_time"].dt.hour
    data["departure_month"] = data["departure_time"].dt.month
    data["departure_dayofweek"] = data["departure_time"].dt.dayofweek

    for column in NUMERIC_FEATURES:
        data[column] = pd.to_numeric(data.get(column, np.nan), errors="coerce")

    for column in CATEGORICAL_FEATURES:
        data[column] = data.get(column, "unknown")
        data[column] = data[column].fillna("unknown").astype(str)

    return data[NUMERIC_FEATURES + CATEGORICAL_FEATURES]


@lru_cache(maxsize=1)
def load_prediction_model():
    if not PREDICTION_MODEL_PATH.exists():
        raise PredictionModelUnavailable(f"Modele de prediction absent: {PREDICTION_MODEL_PATH}")
    return joblib.load(PREDICTION_MODEL_PATH)


def predict_co2(payload: PredictionRequest) -> float:
    model = load_prediction_model()
    features = _build_features(payload)
    prediction = float(model.predict(features)[0])
    return round(max(prediction, 0.0), 6)
