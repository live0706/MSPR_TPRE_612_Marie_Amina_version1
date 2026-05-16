from typing import List

from fastapi import APIRouter, Query

from database import fetch_all
from schemas.statistics import CO2RankingItem, TimelineData, VolumeStatsResponse
from utils import ensure_db

router = APIRouter()


@router.get("/api/statistics/timeline", response_model=List[TimelineData])
def get_timeline_data():
    ensure_db()
    query = """
        WITH stats AS (
            SELECT
                y.year,
                COALESCE(SUM(s.passengers), 0.0) AS passengers,
                COALESCE(SUM(s.co2_emissions), 0.0) AS co2_emissions,
                COALESCE(AVG(s.co2_per_passenger), 0.0) AS co2_per_passenger
            FROM dim_years y
            LEFT JOIN facts_country_stats s ON y.year_id = s.year_id
            GROUP BY y.year
        ),
        trains AS (
            SELECT
                y.year,
                COALESCE(COUNT(t.fact_id), 0) AS train_count
            FROM dim_years y
            LEFT JOIN facts_night_trains t ON y.year_id = t.year_id
            GROUP BY y.year
        )
        SELECT
            stats.year,
            stats.passengers,
            stats.co2_emissions,
            stats.co2_per_passenger,
            COALESCE(trains.train_count, 0) AS train_count
        FROM stats
        LEFT JOIN trains ON stats.year = trains.year
        ORDER BY stats.year
    """
    return fetch_all(query)


@router.get("/api/statistics/co2-ranking", response_model=List[CO2RankingItem])
def get_co2_ranking(limit: int = Query(10, ge=1, le=50)):
    ensure_db()
    query = """
        SELECT
            country_name,
            country_code,
            COALESCE(avg_co2_per_passenger, 0.0) AS avg_co2_per_passenger
        FROM dashboard_metrics
        ORDER BY avg_co2_per_passenger ASC, country_name
        LIMIT :limit
    """
    ranking_rows = fetch_all(query, {"limit": limit})
    ranking = []
    for index, row in enumerate(ranking_rows, start=1):
        avg_co2 = float(row["avg_co2_per_passenger"])
        if avg_co2 < 0.5:
            performance = "good"
        elif avg_co2 < 1.0:
            performance = "medium"
        else:
            performance = "bad"

        ranking.append(
            {
                "country_name": row["country_name"],
                "country_code": row["country_code"],
                "avg_co2_per_passenger": avg_co2,
                "ranking": index,
                "performance": performance,
            }
        )
    return ranking


@router.get(
    "/stats/volumes",
    response_model=List[VolumeStatsResponse],
    summary="Consulter les volumes de trajets",
    description="Agrege les trajets par pays et par annee pour suivre les volumes, le mix jour/nuit et les emissions.",
)
def get_volume_stats(
    country_code: str | None = Query(None, pattern="^[A-Z]{2,10}$"),
    year: int | None = Query(None, ge=2010, le=2100),
    limit: int = Query(100, ge=1, le=500),
):
    ensure_db()
    filters = []
    params = {"limit": limit}

    if country_code:
        filters.append("c.country_code = :country_code")
        params["country_code"] = country_code
    if year is not None:
        filters.append("y.year = :year")
        params["year"] = year

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"""
        SELECT
            y.year,
            c.country_code,
            c.country_name,
            COUNT(f.fact_id) AS total_trajets,
            COUNT(*) FILTER (WHERE f.is_night = TRUE) AS night_trajets,
            COUNT(*) FILTER (WHERE f.is_night = FALSE) AS day_trajets,
            COALESCE(AVG(f.distance_km), 0.0) AS avg_distance_km,
            COALESCE(SUM(f.co2_emissions), 0.0) AS total_co2_emissions
        FROM facts_night_trains f
        JOIN dim_countries c ON f.country_id = c.country_id
        JOIN dim_years y ON f.year_id = y.year_id
        {where_clause}
        GROUP BY y.year, c.country_code, c.country_name
        ORDER BY y.year DESC, total_trajets DESC, c.country_name
        LIMIT :limit
    """
    return fetch_all(query, params)
