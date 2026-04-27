from typing import List

from fastapi import APIRouter, HTTPException, Query

from database import fetch_all, fetch_one
from schemas.operators import OperatorResponse, OperatorStatsResponse
from utils import ensure_db

router = APIRouter()


@router.get("/api/operators", response_model=List[OperatorResponse])
def get_operators(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)):
    ensure_db()
    query = """
        SELECT operator_id, operator_name
        FROM dim_operators
        ORDER BY operator_name
        LIMIT :limit OFFSET :skip
    """
    return fetch_all(query, {"skip": skip, "limit": limit})


@router.get("/api/operators/{operator_id}/stats", response_model=OperatorStatsResponse)
def get_operator_stats(operator_id: int):
    ensure_db()
    operator = fetch_one(
        "SELECT operator_id, operator_name FROM dim_operators WHERE operator_id = :operator_id",
        {"operator_id": operator_id},
    )
    if operator is None:
        raise HTTPException(status_code=404, detail="Operateur non trouve")

    total_trains = fetch_one(
        "SELECT COUNT(*) AS total_trains FROM facts_night_trains WHERE operator_id = :operator_id",
        {"operator_id": operator_id},
    )
    countries = fetch_all(
        """
        SELECT DISTINCT c.country_name
        FROM facts_night_trains f
        JOIN dim_countries c ON f.country_id = c.country_id
        WHERE f.operator_id = :operator_id
        ORDER BY c.country_name
        """,
        {"operator_id": operator_id},
    )

    country_names = [row["country_name"] for row in countries]
    return {
        "operator_id": operator["operator_id"],
        "operator_name": operator["operator_name"],
        "total_trains": int(total_trains["total_trains"]) if total_trains else 0,
        "countries_served": country_names,
        "countries_count": len(country_names),
    }
