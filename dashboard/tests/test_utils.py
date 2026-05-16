import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_DIR = REPO_ROOT / "dashboard"
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))

from utils import build_trajet_params, normalize_status_label


def test_build_trajet_params_filters_empty_values():
    params = build_trajet_params(
        country_code="Tous",
        operator_name="Tous",
        year="Tous",
        service_type="Tous",
        search="",
        limit=150,
    )

    assert params == {"limit": 150}


def test_build_trajet_params_with_values():
    params = build_trajet_params(
        country_code="FR",
        operator_name="SNCF",
        year="2026",
        service_type="Nuit",
        search="Paris",
    )

    assert params["country_code"] == "FR"
    assert params["operator_name"] == "SNCF"
    assert params["year"] == 2026
    assert params["service_type"] == "Nuit"
    assert params["search"] == "Paris"


def test_normalize_status_label():
    assert normalize_status_label("ok") == "Operationnel"
    assert normalize_status_label("degraded") == "Degrade"
    assert normalize_status_label("error") == "Critique"
    assert normalize_status_label("something-else") == "Inconnu"
