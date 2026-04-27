from typing import List

from fastapi import APIRouter

from database import fetch_all, fetch_one
from schemas.statistics import DashboardMetricsResponse, KPIsResponse
from utils import ensure_db

router = APIRouter()


@router.get("/api/dashboard/metrics", response_model=List[DashboardMetricsResponse])
def get_dashboard_metrics():
    ensure_db()
    query = """
        SELECT
            country_name,
            country_code,
            COALESCE(avg_passengers, 0.0) AS avg_passengers,
            COALESCE(avg_co2_emissions, 0.0) AS avg_co2_emissions,
            COALESCE(avg_co2_per_passenger, 0.0) AS avg_co2_per_passenger
        FROM dashboard_metrics
        ORDER BY country_name
    """
    return fetch_all(query)


@router.get("/api/dashboard/kpis", response_model=KPIsResponse)
def get_dashboard_kpis():
    ensure_db()
    total_countries = fetch_one("SELECT COUNT(*) AS total_countries FROM dim_countries")
    total_trains = fetch_one("SELECT COUNT(*) AS total_trains FROM facts_night_trains")
    total_operators = fetch_one("SELECT COUNT(*) AS total_operators FROM dim_operators")
    year_bounds = fetch_one("SELECT MIN(year) AS min_year, MAX(year) AS max_year FROM dim_years")
    aggregates = fetch_one(
        """
        SELECT
            COALESCE(AVG(co2_per_passenger), 0.0) AS avg_co2_per_passenger,
            COALESCE(SUM(passengers), 0.0) AS total_passengers,
            COALESCE(SUM(co2_emissions), 0.0) AS total_co2_emissions
        FROM facts_country_stats
        """
    )

    min_year = year_bounds["min_year"] if year_bounds and year_bounds["min_year"] is not None else None
    max_year = year_bounds["max_year"] if year_bounds and year_bounds["max_year"] is not None else None
    years_covered = f"{min_year}-{max_year}" if min_year is not None and max_year is not None else "Pas de donnees"

    return {
        "total_countries": int(total_countries["total_countries"]) if total_countries else 0,
        "total_trains": int(total_trains["total_trains"]) if total_trains else 0,
        "total_operators": int(total_operators["total_operators"]) if total_operators else 0,
        "years_covered": years_covered,
        "avg_co2_per_passenger": float(aggregates["avg_co2_per_passenger"]) if aggregates else 0.0,
        "total_passengers": float(aggregates["total_passengers"]) if aggregates else 0.0,
        "total_co2_emissions": float(aggregates["total_co2_emissions"]) if aggregates else 0.0,
    }
