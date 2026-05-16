from fastapi import APIRouter

from config import APP_NAME, APP_VERSION, ENABLE_PROMETHEUS, GRAFANA_URL, PROMETHEUS_URL
from database import fetch_one, ping_database
from schemas.health import MonitoringSummary
from utils import ensure_db

router = APIRouter(tags=["Monitoring"])


@router.get(
    "/api/monitoring/summary",
    response_model=MonitoringSummary,
    summary="Resume d'observabilite",
    description="Expose un resume exploitable par le dashboard sur la sante, les volumes et les liens de supervision.",
)
def get_monitoring_summary():
    ensure_db()

    counts = fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM trips) AS total_trips,
            (SELECT COUNT(*) FROM dim_countries) AS total_countries,
            (SELECT COUNT(*) FROM dim_operators) AS total_operators,
            (SELECT MAX(fetched_at) FROM ingestions) AS latest_ingestion_at
        """
    ) or {}

    return {
        "api_name": APP_NAME,
        "api_version": APP_VERSION,
        "database_connected": ping_database(),
        "prometheus_enabled": ENABLE_PROMETHEUS,
        "metrics_endpoint": "/metrics",
        "grafana_url": GRAFANA_URL,
        "prometheus_url": PROMETHEUS_URL,
        "total_trips": int(counts.get("total_trips") or 0),
        "total_countries": int(counts.get("total_countries") or 0),
        "total_operators": int(counts.get("total_operators") or 0),
        "latest_ingestion_at": counts.get("latest_ingestion_at"),
    }
