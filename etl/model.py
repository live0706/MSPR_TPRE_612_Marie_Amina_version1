import json
import logging
import os
from datetime import datetime

import numpy as np

logger = logging.getLogger()


def _train_test_split(x, y, test_ratio=0.2, seed=42):
    rng = np.random.default_rng(seed)
    idx = np.arange(len(x))
    rng.shuffle(idx)
    split = int(len(idx) * (1 - test_ratio))
    train_idx = idx[:split]
    test_idx = idx[split:]
    return x[train_idx], x[test_idx], y[train_idx], y[test_idx]


def _r2_score(y_true, y_pred):
    if len(y_true) == 0:
        return 0.0
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 0.0
    return 1 - (ss_res / ss_tot)


def train_co2_model(df, output_dir):
    """
    Train a simple linear model: co2_emissions = a * distance_km + b.
    Stores coefficients and metrics in JSON for auditability.
    """
    if df is None or df.empty:
        logger.warning("Model training skipped: empty dataframe.")
        return None

    if "distance_km" not in df.columns or "co2_emissions" not in df.columns:
        logger.warning("Model training skipped: required columns missing.")
        return None

    data = df[["distance_km", "co2_emissions"]].dropna()
    data = data[(data["distance_km"] > 0) & (data["co2_emissions"] >= 0)]

    if len(data) < 10:
        logger.warning("Model training skipped: not enough data points.")
        return None

    x = data["distance_km"].to_numpy(dtype=float)
    y = data["co2_emissions"].to_numpy(dtype=float)

    x_train, x_test, y_train, y_test = _train_test_split(x, y)

    # Fit linear regression via numpy (degree 1).
    a, b = np.polyfit(x_train, y_train, 1)
    y_pred = a * x_test + b

    mae = float(np.mean(np.abs(y_test - y_pred)))
    rmse = float(np.sqrt(np.mean((y_test - y_pred) ** 2)))
    r2 = float(_r2_score(y_test, y_pred))

    os.makedirs(output_dir, exist_ok=True)
    metrics = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "model": "linear_regression_numpy",
        "features": ["distance_km"],
        "target": "co2_emissions",
        "coefficients": {"a": float(a), "b": float(b)},
        "metrics": {"mae": mae, "rmse": rmse, "r2": r2},
        "data_points": int(len(data)),
    }

    output_path = os.path.join(output_dir, "model_metrics.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Model metrics written: {output_path}")
    return output_path
