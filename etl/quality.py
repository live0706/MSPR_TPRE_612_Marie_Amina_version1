import json
import logging
import os
from datetime import datetime

logger = logging.getLogger()


def _safe_rate(numerator, denominator):
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)


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
        service_type_counts = df["service_type"].value_counts(dropna=False).to_dict()

    co2_zero_or_missing = 0
    if "co2_emissions" in df.columns:
        co2_zero_or_missing = int(df["co2_emissions"].isna().sum() + (df["co2_emissions"] == 0).sum())

    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_rows": total_rows,
        "duplicate_trip_ids": duplicate_trip_ids,
        "missing_by_column": missing_by_col,
        "missing_rate_by_column": missing_rate,
        "service_type_counts": service_type_counts,
        "co2_zero_or_missing": co2_zero_or_missing,
    }

    output_path = os.path.join(output_dir, "quality_report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Quality report written: {output_path}")
    return output_path
