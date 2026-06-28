from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


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
TARGET = "co2_emissions"


@dataclass(frozen=True)
class DatasetSplit:
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame


def load_dataset(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)


def prepare_features(df: pd.DataFrame, require_target: bool = True) -> pd.DataFrame:
    data = df.copy()

    for column in ["departure_time", "arrival_time"]:
        if column in data.columns:
            data[column] = pd.to_datetime(data[column], errors="coerce")

    if "departure_time" in data.columns and "arrival_time" in data.columns:
        duration = (data["arrival_time"] - data["departure_time"]).dt.total_seconds() / 3600
        data["duration_hours"] = duration.where(duration >= 0, duration + 24)
    else:
        data["duration_hours"] = np.nan

    if "departure_time" in data.columns:
        data["departure_hour"] = data["departure_time"].dt.hour
        data["departure_month"] = data["departure_time"].dt.month
        data["departure_dayofweek"] = data["departure_time"].dt.dayofweek
    else:
        data["departure_hour"] = np.nan
        data["departure_month"] = np.nan
        data["departure_dayofweek"] = np.nan

    for column in NUMERIC_FEATURES:
        if column not in data.columns:
            data[column] = np.nan
        data[column] = pd.to_numeric(data[column], errors="coerce")

    for column in CATEGORICAL_FEATURES:
        if column not in data.columns:
            data[column] = "unknown"
        data[column] = data[column].fillna("unknown").astype(str)

    data = data[data["distance_km"] > 0]
    if require_target:
        data[TARGET] = pd.to_numeric(data[TARGET], errors="coerce")
        data = data[data[TARGET].notna() & (data[TARGET] >= 0)]

    return data[NUMERIC_FEATURES + CATEGORICAL_FEATURES + ([TARGET] if require_target else [])]


def split_dataset(df: pd.DataFrame, seed: int = 42) -> DatasetSplit:
    shuffled = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    train_end = int(len(shuffled) * 0.7)
    validation_end = int(len(shuffled) * 0.85)
    return DatasetSplit(
        train=shuffled.iloc[:train_end].copy(),
        validation=shuffled.iloc[train_end:validation_end].copy(),
        test=shuffled.iloc[validation_end:].copy(),
    )
