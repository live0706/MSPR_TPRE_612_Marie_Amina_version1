from __future__ import annotations

from datetime import datetime, timezone

from config import APP_ENV, APP_VERSION, MODEL_METRICS_PATH, QUALITY_REPORT_PATH
from database import ping_database


def component_status(file_exists: bool, ok_detail: str, ko_detail: str) -> dict[str, str]:
    if file_exists:
        return {"status": "ok", "detail": ok_detail}
    return {"status": "degraded", "detail": ko_detail}


def build_health_payload() -> dict:
    database_is_up = ping_database()
    quality_report_exists = QUALITY_REPORT_PATH.exists()
    model_metrics_exists = MODEL_METRICS_PATH.exists()

    statuses = [database_is_up, quality_report_exists, model_metrics_exists]
    if all(statuses):
        global_status = "ok"
    elif database_is_up:
        global_status = "degraded"
    else:
        global_status = "error"

    return {
        "status": global_status,
        "environment": APP_ENV,
        "version": APP_VERSION,
        "timestamp": datetime.now(timezone.utc),
        "database": {
            "status": "ok" if database_is_up else "error",
            "detail": "Connexion PostgreSQL operationnelle."
            if database_is_up
            else "Connexion PostgreSQL indisponible.",
        },
        "quality_report": component_status(
            quality_report_exists,
            "Rapport de qualite disponible.",
            "Rapport de qualite absent.",
        ),
        "model_metrics": component_status(
            model_metrics_exists,
            "Metriques modele disponibles.",
            "Metriques modele absentes.",
        ),
    }


def application_health_score() -> float:
    return 1.0 if build_health_payload()["status"] == "ok" else 0.0


def quality_report_score() -> float:
    return 1.0 if QUALITY_REPORT_PATH.exists() else 0.0


def model_metrics_score() -> float:
    return 1.0 if MODEL_METRICS_PATH.exists() else 0.0
