from __future__ import annotations

from prometheus_client import Gauge

from database import fetch_one, ping_database

_METRICS_REGISTERED = False


def _query_numeric_value(query: str) -> float:
    try:
        row = fetch_one(query) or {}
        value = row.get("value")
        if value is None:
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def register_business_metrics() -> None:
    global _METRICS_REGISTERED
    if _METRICS_REGISTERED:
        return

    Gauge(
        "obrail_database_connected",
        "Etat de connexion PostgreSQL de l'application ObRail.",
    ).set_function(lambda: 1.0 if ping_database() else 0.0)

    Gauge(
        "obrail_total_trips",
        "Nombre total de trajets references dans l'application ObRail.",
    ).set_function(lambda: _query_numeric_value("SELECT COUNT(*) AS value FROM trips"))

    Gauge(
        "obrail_total_countries",
        "Nombre total de pays references dans l'application ObRail.",
    ).set_function(lambda: _query_numeric_value("SELECT COUNT(*) AS value FROM dim_countries"))

    Gauge(
        "obrail_total_operators",
        "Nombre total d'operateurs references dans l'application ObRail.",
    ).set_function(lambda: _query_numeric_value("SELECT COUNT(*) AS value FROM dim_operators"))

    Gauge(
        "obrail_total_night_trips",
        "Nombre total de trajets de nuit references dans l'application ObRail.",
    ).set_function(
        lambda: _query_numeric_value(
            "SELECT COUNT(*) AS value FROM facts_night_trains WHERE is_night = TRUE"
        )
    )

    Gauge(
        "obrail_total_day_trips",
        "Nombre total de trajets de jour references dans l'application ObRail.",
    ).set_function(
        lambda: _query_numeric_value(
            "SELECT COUNT(*) AS value FROM facts_night_trains WHERE is_night = FALSE"
        )
    )

    Gauge(
        "obrail_latest_ingestion_timestamp_seconds",
        "Horodatage Unix de la derniere ingestion ObRail.",
    ).set_function(
        lambda: _query_numeric_value(
            "SELECT COALESCE(EXTRACT(EPOCH FROM MAX(fetched_at)), 0) AS value FROM ingestions"
        )
    )

    _METRICS_REGISTERED = True
