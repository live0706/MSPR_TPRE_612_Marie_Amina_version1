from typing import List, Optional

from fastapi import APIRouter, Query

from database import fetch_all, fetch_one
from schemas.trains import LegacyTrainSchema
from utils import ensure_db

router = APIRouter()


@router.get("/trains", response_model=List[LegacyTrainSchema])
def get_trains(
    limit: int = Query(20, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service_type: Optional[str] = Query(None, pattern="^(Jour|Nuit)$"),
):
    ensure_db()
    query = """
        SELECT
            t.trip_id,
            o.name AS operator_name,
            so.name AS origin_city,
            sd.name AS destination_city,
            CAST(t.departure_time AS TEXT) AS departure_time,
            CAST(t.arrival_time AS TEXT) AS arrival_time,
            t.service_type,
            t.train_type,
            r.distance_km,
            t.co2_emissions
        FROM trips t
        LEFT JOIN routes r ON t.route_id = r.route_id
        LEFT JOIN operators o ON r.operator_id = o.operator_id
        LEFT JOIN stations so ON r.origin_station_id = so.station_id
        LEFT JOIN stations sd ON r.destination_station_id = sd.station_id
    """
    params = {"limit": limit, "offset": offset}
    if service_type:
        query += " WHERE t.service_type = :service_type"
        params["service_type"] = service_type
    query += " ORDER BY t.departure_time DESC LIMIT :limit OFFSET :offset"
    return fetch_all(query, params)


@router.get("/stats")
def get_stats():
    ensure_db()
    total = fetch_one("SELECT COUNT(*) AS total_trains FROM trips")
    night = fetch_one("SELECT COUNT(*) AS night_trains FROM trips WHERE service_type = 'Nuit'")
    day = fetch_one("SELECT COUNT(*) AS day_trains FROM trips WHERE service_type = 'Jour'")

    total_trains = int(total["total_trains"]) if total else 0
    night_trains = int(night["night_trains"]) if night else 0
    day_trains = int(day["day_trains"]) if day else 0

    return {
        "total_trains": total_trains,
        "breakdown": {
            "night_trains": night_trains,
            "day_trains": day_trains,
            "night_share_percentage": round((night_trains / total_trains) * 100, 2) if total_trains else 0.0,
        },
    }
