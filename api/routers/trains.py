from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from database import fetch_all, fetch_one
from schemas.trains import TrainResponse
from utils import ensure_db

router = APIRouter()


def _fetch_trains(is_night: Optional[bool], skip: int, limit: int, country_code: Optional[str], operator_name: Optional[str], year: Optional[int]):
    filters = []
    params = {"skip": skip, "limit": limit}

    if is_night is not None:
        filters.append("f.is_night = :is_night")
        params["is_night"] = is_night
    if country_code:
        filters.append("c.country_code = :country_code")
        params["country_code"] = country_code
    if operator_name:
        filters.append("o.operator_name ILIKE :operator_name")
        params["operator_name"] = f"%{operator_name}%"
    if year:
        filters.append("y.year = :year")
        params["year"] = year

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"""
        SELECT
            f.fact_id,
            f.trip_id,
            f.route_id,
            f.night_train,
            c.country_name,
            c.country_code,
            o.operator_name,
            y.year,
            f.is_night,
            COALESCE(f.distance_km, 0.0) AS distance_km,
            COALESCE(f.co2_emissions, 0.0) AS co2_emissions
        FROM facts_night_trains f
        JOIN dim_countries c ON f.country_id = c.country_id
        JOIN dim_years y ON f.year_id = y.year_id
        JOIN dim_operators o ON f.operator_id = o.operator_id
        {where_clause}
        ORDER BY y.year DESC, f.night_train
        LIMIT :limit OFFSET :skip
    """
    return fetch_all(query, params)


@router.get("/api/night-trains", response_model=List[TrainResponse])
def get_all_trains(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    country_code: Optional[str] = None,
    operator_name: Optional[str] = None,
    year: Optional[int] = None,
):
    ensure_db()
    return _fetch_trains(None, skip, limit, country_code, operator_name, year)


@router.get("/api/night-trains/night", response_model=List[TrainResponse])
def get_night_trains(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    country_code: Optional[str] = None,
    operator_name: Optional[str] = None,
    year: Optional[int] = None,
):
    ensure_db()
    return _fetch_trains(True, skip, limit, country_code, operator_name, year)


@router.get("/api/night-trains/day", response_model=List[TrainResponse])
def get_day_trains(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    country_code: Optional[str] = None,
    operator_name: Optional[str] = None,
    year: Optional[int] = None,
):
    ensure_db()
    return _fetch_trains(False, skip, limit, country_code, operator_name, year)


@router.get("/api/night-trains/by-operator/{operator_id}", response_model=List[TrainResponse])
def get_trains_by_operator(operator_id: int, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)):
    ensure_db()
    operator = fetch_one("SELECT operator_id FROM dim_operators WHERE operator_id = :operator_id", {"operator_id": operator_id})
    if operator is None:
        raise HTTPException(status_code=404, detail="Operateur non trouve")
    query = """
        SELECT
            f.fact_id,
            f.trip_id,
            f.route_id,
            f.night_train,
            c.country_name,
            c.country_code,
            o.operator_name,
            y.year,
            f.is_night,
            COALESCE(f.distance_km, 0.0) AS distance_km,
            COALESCE(f.co2_emissions, 0.0) AS co2_emissions
        FROM facts_night_trains f
        JOIN dim_countries c ON f.country_id = c.country_id
        JOIN dim_years y ON f.year_id = y.year_id
        JOIN dim_operators o ON f.operator_id = o.operator_id
        WHERE f.operator_id = :operator_id
        ORDER BY y.year DESC, f.night_train
        LIMIT :limit OFFSET :skip
    """
    return fetch_all(query, {"operator_id": operator_id, "skip": skip, "limit": limit})


@router.get("/api/geographic/coverage")
def get_geographic_coverage():
    ensure_db()
    query = """
        SELECT
            c.country_name,
            c.country_code,
            COUNT(f.fact_id) AS train_count
        FROM dim_countries c
        JOIN facts_night_trains f ON c.country_id = f.country_id
        GROUP BY c.country_id, c.country_name, c.country_code
        ORDER BY train_count DESC, c.country_name
    """
    coverage = fetch_all(query)
    return {
        "total_countries_covered": len(coverage),
        "coverage_by_country": coverage,
    }
