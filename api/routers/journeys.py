from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query

from database import fetch_all, fetch_one
from schemas.journeys import JourneyDetail, JourneySummary
from utils import ensure_db

router = APIRouter(tags=["Trajets"])

ALLOWED_SORT_FIELDS = {
    "departure_time": "t.departure_time",
    "arrival_time": "t.arrival_time",
    "distance_km": "r.distance_km",
    "co2_emissions": "t.co2_emissions",
    "created_at": "t.created_at",
}


def _base_trajets_query():
    return """
        SELECT
            t.trip_id,
            r.route_id,
            o.name AS operator_name,
            so.name AS origin_city,
            so.country AS origin_country,
            sd.name AS destination_city,
            sd.country AS destination_country,
            t.departure_time,
            t.arrival_time,
            t.service_type,
            t.train_type,
            COALESCE(r.distance_km, 0.0) AS distance_km,
            COALESCE(t.co2_emissions, 0.0) AS co2_emissions,
            COALESCE(c.country_code, src.country_code, 'ZZ') AS country_code,
            COALESCE(c.country_name, src.country_name, 'Unknown') AS country_name,
            src.source_key,
            src.name AS source_name,
            src.source_type,
            src.provider AS source_provider,
            src.license AS source_license,
            t.created_at
        FROM trips t
        LEFT JOIN routes r ON t.route_id = r.route_id
        LEFT JOIN operators o ON r.operator_id = o.operator_id
        LEFT JOIN stations so ON r.origin_station_id = so.station_id
        LEFT JOIN stations sd ON r.destination_station_id = sd.station_id
        LEFT JOIN sources src ON t.source_id = src.source_id
        LEFT JOIN facts_night_trains f ON f.trip_id = t.trip_id
        LEFT JOIN dim_countries c ON f.country_id = c.country_id
        LEFT JOIN dim_years y ON f.year_id = y.year_id
    """


@router.get(
    "/trajets",
    response_model=list[JourneySummary],
    summary="Lister les trajets ferroviaires",
    description="Retourne les trajets filtres par pays, operateur, annee, type de service ou recherche libre.",
)
def list_trajets(
    limit: int = Query(50, ge=1, le=500, description="Nombre maximal de trajets retournes."),
    offset: int = Query(0, ge=0, description="Decalage pour la pagination."),
    country_code: Optional[str] = Query(None, pattern="^[A-Z]{2,10}$"),
    operator_name: Optional[str] = Query(None, min_length=2, max_length=100),
    year: Optional[int] = Query(None, ge=2010, le=2100),
    service_type: Optional[str] = Query(None, pattern="^(Jour|Nuit)$"),
    search: Optional[str] = Query(None, min_length=2, max_length=120),
    sort_by: str = Query("departure_time", pattern="^(departure_time|arrival_time|distance_km|co2_emissions|created_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
):
    ensure_db()

    filters = []
    params = {"limit": limit, "offset": offset}

    if country_code:
        filters.append("COALESCE(c.country_code, src.country_code, 'ZZ') = :country_code")
        params["country_code"] = country_code
    if operator_name:
        filters.append("o.name ILIKE :operator_name")
        params["operator_name"] = f"%{operator_name.strip()}%"
    if year is not None:
        filters.append("EXTRACT(YEAR FROM t.departure_time) = :year")
        params["year"] = year
    if service_type:
        filters.append("t.service_type = :service_type")
        params["service_type"] = service_type
    if search:
        filters.append(
            "("
            "t.trip_id ILIKE :search OR "
            "o.name ILIKE :search OR "
            "so.name ILIKE :search OR "
            "sd.name ILIKE :search"
            ")"
        )
        params["search"] = f"%{search.strip()}%"

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    order_clause = ALLOWED_SORT_FIELDS.get(sort_by, ALLOWED_SORT_FIELDS["departure_time"])
    direction = "ASC" if sort_order == "asc" else "DESC"

    query = f"""
        {_base_trajets_query()}
        {where_clause}
        ORDER BY {order_clause} {direction}, t.trip_id
        LIMIT :limit OFFSET :offset
    """
    return fetch_all(query, params)


@router.get(
    "/trajets/{trip_id}",
    response_model=JourneyDetail,
    summary="Consulter le detail d'un trajet",
    description="Retourne le detail complet d'un trajet a partir de son identifiant technique.",
)
def get_trajet(
    trip_id: str = Path(..., min_length=3, max_length=200, pattern=r"^[A-Za-z0-9:_\-.]+$"),
):
    ensure_db()
    query = f"""
        {_base_trajets_query()}
        WHERE t.trip_id = :trip_id
        LIMIT 1
    """
    trajet = fetch_one(query, {"trip_id": trip_id})
    if trajet is None:
        raise HTTPException(status_code=404, detail="Trajet non trouve.")
    return trajet
