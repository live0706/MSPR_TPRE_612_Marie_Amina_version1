import json
import logging
import os
from datetime import datetime

logger = logging.getLogger()


def _safe_rate(numerator, denominator):
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)


def _top_counts(series, limit=10):
    if series is None:
        return {}
    clean_series = series.dropna().astype(str)
    if clean_series.empty:
        return {}
    return {key: int(value) for key, value in clean_series.value_counts().head(limit).items()}


def write_quality_report(df, output_dir):
    """
    Compute basic data-quality metrics and write them to JSON.
    """
    if df is None or df.empty:
        logger.warning("Quality report skipped: empty dataframe.")
        return None

    os.makedirs(output_dir, exist_ok=True)

    total_rows = len(df)
    missing_by_col = df.isna().sum().to_dict()
    missing_rate = {k: _safe_rate(v, total_rows) for k, v in missing_by_col.items()}

    duplicate_trip_ids = 0
    if "trip_id" in df.columns:
        duplicate_trip_ids = int(df.duplicated(subset=["trip_id"]).sum())

    service_type_counts = {}
    if "service_type" in df.columns:
        service_type_counts = {key: int(value) for key, value in df["service_type"].value_counts(dropna=False).items()}

    co2_zero_or_missing = 0
    if "co2_emissions" in df.columns:
        co2_zero_or_missing = int(df["co2_emissions"].isna().sum() + (df["co2_emissions"] == 0).sum())

    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_rows": total_rows,
        "duplicate_trip_ids": duplicate_trip_ids,
        "distinct_operators": int(df["operator_name"].dropna().nunique()) if "operator_name" in df.columns else 0,
        "distinct_countries": int(df["country"].dropna().nunique()) if "country" in df.columns else 0,
        "distinct_sources": int(df["source_origin"].dropna().nunique()) if "source_origin" in df.columns else 0,
        "missing_by_column": missing_by_col,
        "missing_rate_by_column": missing_rate,
        "service_type_counts": service_type_counts,
        "co2_zero_or_missing": co2_zero_or_missing,
        "top_countries": _top_counts(df["country"]) if "country" in df.columns else {},
        "top_operators": _top_counts(df["operator_name"]) if "operator_name" in df.columns else {},
        "top_sources": _top_counts(df["source_origin"]) if "source_origin" in df.columns else {},
    }

    output_path = os.path.join(output_dir, "quality_report.json")
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    logger.info(f"Quality report written: {output_path}")
    return output_path
