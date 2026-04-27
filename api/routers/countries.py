from typing import List, Optional

from fastapi import APIRouter, Query

from database import fetch_all
from schemas.countries import CountryResponse, CountryStatsResponse
from utils import ensure_db

router = APIRouter()


@router.get("/api/countries", response_model=List[CountryResponse])
def get_countries(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)):
    ensure_db()
    query = """
        SELECT country_id, country_code, country_name
        FROM dim_countries
        ORDER BY country_name
        LIMIT :limit OFFSET :skip
    """
    return fetch_all(query, {"skip": skip, "limit": limit})


@router.get("/api/countries/stats", response_model=List[CountryStatsResponse])
def get_country_stats(
    country_code: Optional[str] = None,
    year: Optional[int] = None,
    min_passengers: Optional[float] = None,
    max_passengers: Optional[float] = None,
    min_co2_per_passenger: Optional[float] = None,
    max_co2_per_passenger: Optional[float] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    ensure_db()
    filters = []
    params = {"skip": skip, "limit": limit}

    if country_code:
        filters.append("c.country_code = :country_code")
        params["country_code"] = country_code
    if year:
        filters.append("y.year = :year")
        params["year"] = year
    if min_passengers is not None:
        filters.append("f.passengers >= :min_passengers")
        params["min_passengers"] = min_passengers
    if max_passengers is not None:
        filters.append("f.passengers <= :max_passengers")
        params["max_passengers"] = max_passengers
    if min_co2_per_passenger is not None:
        filters.append("f.co2_per_passenger >= :min_co2_per_passenger")
        params["min_co2_per_passenger"] = min_co2_per_passenger
    if max_co2_per_passenger is not None:
        filters.append("f.co2_per_passenger <= :max_co2_per_passenger")
        params["max_co2_per_passenger"] = max_co2_per_passenger

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"""
        SELECT
            f.stats_id,
            f.passengers,
            f.co2_emissions,
            f.co2_per_passenger,
            c.country_name,
            c.country_code,
            y.year
        FROM facts_country_stats f
        JOIN dim_countries c ON f.country_id = c.country_id
        JOIN dim_years y ON f.year_id = y.year_id
        {where_clause}
        ORDER BY y.year DESC, c.country_name
        LIMIT :limit OFFSET :skip
    """
    return fetch_all(query, params)
