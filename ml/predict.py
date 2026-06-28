from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd

try:
    from features import prepare_features
except ModuleNotFoundError:
    from ml.features import prepare_features


DEFAULT_MODEL_PATH = Path("ml/models/co2_emissions_model.joblib")


def predict(payload: dict, model_path: Path = DEFAULT_MODEL_PATH) -> float:
    model = joblib.load(model_path)
    features = prepare_features(pd.DataFrame([payload]), require_target=False)
    return float(model.predict(features)[0])


def main() -> None:
    parser = argparse.ArgumentParser(description="Predict CO2 emissions for one rail trip.")
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--input-json", type=Path)
    parser.add_argument("--distance-km", type=float)
    parser.add_argument("--operator-name", default="unknown")
    parser.add_argument("--service-type", default="Jour")
    parser.add_argument("--train-type", default="Rail")
    parser.add_argument("--country", default="unknown")
    parser.add_argument("--departure-time", default=None)
    args = parser.parse_args()

    if args.input_json:
        payload = json.loads(args.input_json.read_text(encoding="utf-8"))
    else:
        payload = {
            "distance_km": args.distance_km,
            "operator_name": args.operator_name,
            "service_type": args.service_type,
            "train_type": args.train_type,
            "country": args.country,
            "departure_time": args.departure_time,
        }

    prediction = predict(payload, args.model_path)
    print(json.dumps({"predicted_co2_emissions": round(prediction, 6), "unit": "kgCO2e"}, indent=2))


if __name__ == "__main__":
    main()
