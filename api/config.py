import os
from pathlib import Path


def _get_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _get_origins() -> list[str]:
    raw_value = os.getenv("CORS_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501")
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


APP_NAME = "ObRail Europe API"
APP_VERSION = os.getenv("APP_VERSION", "2.1.0")
APP_DESCRIPTION = (
    "API industrialisee pour consulter les trajets ferroviaires europeens, "
    "les statistiques de volumes et l'etat de sante de la plateforme."
)
APP_ENV = os.getenv("APP_ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
ENABLE_PROMETHEUS = _get_bool("ENABLE_PROMETHEUS", True)
CORS_ORIGINS = _get_origins()

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
QUALITY_REPORT_PATH = Path(os.getenv("QUALITY_REPORT_PATH", str(DATA_DIR / "processed" / "quality_report.json")))
MODEL_METRICS_PATH = Path(os.getenv("MODEL_METRICS_PATH", str(DATA_DIR / "processed" / "model_metrics.json")))
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
