import os

from fastapi import APIRouter

from database import fetch_all
from utils import ensure_db, read_json_file

router = APIRouter()

QUALITY_REPORT_PATH = os.getenv("QUALITY_REPORT_PATH", "/app/data/processed/quality_report.json")
MODEL_METRICS_PATH = os.getenv("MODEL_METRICS_PATH", "/app/data/processed/model_metrics.json")


@router.get("/api/metadata/quality")
def get_quality_report():
    quality_report = read_json_file(QUALITY_REPORT_PATH)
    model_metrics = read_json_file(MODEL_METRICS_PATH)
    return {
        "quality_report": quality_report or {},
        "model_metrics": model_metrics or {},
    }


@router.get("/api/metadata/sources")
def get_data_sources():
    ensure_db()
    query = """
        SELECT
            source_id AS id,
            source_key,
            name,
            url,
            source_type,
            provider,
            license,
            last_seen
        FROM sources
        ORDER BY source_key
    """
    return {"sources": fetch_all(query)}
