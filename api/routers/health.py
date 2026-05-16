from datetime import datetime, timezone

from fastapi import APIRouter

from config import APP_ENV, APP_VERSION, MODEL_METRICS_PATH, QUALITY_REPORT_PATH
from database import ping_database
from schemas.health import HealthResponse

router = APIRouter(tags=["Sante"])


def _component_status(file_exists: bool, ok_detail: str, ko_detail: str):
    if file_exists:
        return {"status": "ok", "detail": ok_detail}
    return {"status": "degraded", "detail": ko_detail}


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Verifier l'etat de sante de l'API",
    description="Controle la disponibilite de l'API, de la base PostgreSQL et des fichiers de qualite/modeles.",
)
def health_check():
    database_is_up = ping_database()
    quality_report_exists = QUALITY_REPORT_PATH.exists()
    model_metrics_exists = MODEL_METRICS_PATH.exists()

    statuses = [
        database_is_up,
        quality_report_exists,
        model_metrics_exists,
    ]
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
            "detail": "Connexion PostgreSQL operationnelle." if database_is_up else "Connexion PostgreSQL indisponible.",
        },
        "quality_report": _component_status(
            quality_report_exists,
            "Rapport de qualite disponible.",
            "Rapport de qualite absent.",
        ),
        "model_metrics": _component_status(
            model_metrics_exists,
            "Metriques modele disponibles.",
            "Metriques modele absentes.",
        ),
    }
