from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import RandomizedSearchCV
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from features import CATEGORICAL_FEATURES, NUMERIC_FEATURES, TARGET, load_dataset, prepare_features, split_dataset
except ModuleNotFoundError:
    from ml.features import CATEGORICAL_FEATURES, NUMERIC_FEATURES, TARGET, load_dataset, prepare_features, split_dataset


DEFAULT_DATASET = Path("data/processed/trips_cleaned_final.csv")
DEFAULT_OUTPUT_DIR = Path("ml/reports")
DEFAULT_MODEL_DIR = Path("ml/models")
DEFAULT_SERVING_MODEL_PATH = Path("data/processed/co2_emissions_model.joblib")


def build_preprocessor() -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", min_frequency=10)),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )


def build_pipeline(model) -> Pipeline:
    return Pipeline(steps=[("preprocessor", build_preprocessor()), ("model", model)])


def evaluate_model(name: str, model: Pipeline, x, y) -> dict:
    predictions = model.predict(x)
    rmse = np.sqrt(mean_squared_error(y, predictions))
    return {
        "model": name,
        "mae": float(mean_absolute_error(y, predictions)),
        "rmse": float(rmse),
        "r2": float(r2_score(y, predictions)),
    }


def train_models(
    dataset_path: Path,
    output_dir: Path,
    model_dir: Path,
    serving_model_path: Path = DEFAULT_SERVING_MODEL_PATH,
    sample_size: int | None = None,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)

    raw_df = load_dataset(dataset_path)
    prepared = prepare_features(raw_df, require_target=True)
    if sample_size and len(prepared) > sample_size:
        prepared = prepared.sample(n=sample_size, random_state=42)

    splits = split_dataset(prepared)
    x_train, y_train = splits.train.drop(columns=[TARGET]), splits.train[TARGET]
    x_validation, y_validation = splits.validation.drop(columns=[TARGET]), splits.validation[TARGET]
    x_test, y_test = splits.test.drop(columns=[TARGET]), splits.test[TARGET]

    candidates = {
        "linear_regression": build_pipeline(LinearRegression()),
        "ridge": build_pipeline(Ridge(random_state=42)),
        "random_forest": build_pipeline(RandomForestRegressor(random_state=42, n_jobs=-1)),
        "hist_gradient_boosting": build_pipeline(HistGradientBoostingRegressor(random_state=42)),
        "mlp": build_pipeline(MLPRegressor(random_state=42, max_iter=300, early_stopping=True)),
    }

    search_spaces = {
        "ridge": {"model__alpha": [0.01, 0.1, 1.0, 10.0, 100.0]},
        "random_forest": {
            "model__n_estimators": [80, 150, 250],
            "model__max_depth": [8, 16, 24, None],
            "model__min_samples_leaf": [1, 3, 5],
        },
        "hist_gradient_boosting": {
            "model__learning_rate": [0.03, 0.05, 0.1],
            "model__max_iter": [100, 200, 300],
            "model__max_leaf_nodes": [15, 31, 63],
        },
        "mlp": {
            "model__hidden_layer_sizes": [(32,), (64,), (64, 32)],
            "model__alpha": [0.0001, 0.001, 0.01],
            "model__learning_rate_init": [0.001, 0.003],
        },
    }

    validation_rows = []
    fitted_models = {}
    for name, pipeline in candidates.items():
        if name in search_spaces:
            param_count = 1
            for values in search_spaces[name].values():
                param_count *= len(values)
            estimator = RandomizedSearchCV(
                pipeline,
                search_spaces[name],
                n_iter=min(8, param_count),
                scoring="neg_root_mean_squared_error",
                cv=3,
                random_state=42,
                n_jobs=-1,
            )
            estimator.fit(x_train, y_train)
            fitted = estimator.best_estimator_
            best_params = estimator.best_params_
        else:
            fitted = pipeline.fit(x_train, y_train)
            best_params = {}

        metrics = evaluate_model(name, fitted, x_validation, y_validation)
        metrics["best_params"] = best_params
        validation_rows.append(metrics)
        fitted_models[name] = fitted

    comparison = pd.DataFrame(validation_rows).sort_values(["rmse", "mae"], ascending=True)
    best_name = str(comparison.iloc[0]["model"])
    best_model = fitted_models[best_name]
    test_metrics = evaluate_model(best_name, best_model, x_test, y_test)

    model_path = model_dir / "co2_emissions_model.joblib"
    joblib.dump(best_model, model_path)
    serving_model_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(model_path, serving_model_path)

    comparison_path = output_dir / "model_comparison.csv"
    metrics_path = output_dir / "evaluation_report.json"
    comparison.to_csv(comparison_path, index=False)

    plt.figure(figsize=(9, 5))
    plt.bar(comparison["model"], comparison["rmse"])
    plt.ylabel("RMSE")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plot_path = output_dir / "model_rmse_comparison.png"
    plt.savefig(plot_path, dpi=140)
    plt.close()

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_path": str(dataset_path),
        "rows_used": int(len(prepared)),
        "features": {"numeric": NUMERIC_FEATURES, "categorical": CATEGORICAL_FEATURES},
        "target": TARGET,
        "best_model": best_name,
        "model_path": str(model_path),
        "serving_model_path": str(serving_model_path),
        "validation_metrics": validation_rows,
        "test_metrics": test_metrics,
    }
    metrics_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Train ObRail CO2 prediction models.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--serving-model-path", type=Path, default=DEFAULT_SERVING_MODEL_PATH)
    parser.add_argument("--sample-size", type=int, default=None)
    args = parser.parse_args()

    report = train_models(args.dataset, args.output_dir, args.model_dir, args.serving_model_path, args.sample_size)
    print(json.dumps({"best_model": report["best_model"], "model_path": report["model_path"]}, indent=2))


if __name__ == "__main__":
    main()
