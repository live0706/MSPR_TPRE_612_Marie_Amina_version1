from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class JourneySummary(BaseModel):
    trip_id: str = Field(..., description="Identifiant unique du trajet.")
    route_id: Optional[int] = Field(default=None, description="Identifiant technique de la route.")
    operator_name: Optional[str] = None
    origin_city: Optional[str] = None
    origin_country: Optional[str] = None
    origin_lat: Optional[float] = None
    origin_lon: Optional[float] = None
    destination_city: Optional[str] = None
    destination_country: Optional[str] = None
    destination_lat: Optional[float] = None
    destination_lon: Optional[float] = None
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    service_type: Optional[str] = None
    train_type: Optional[str] = None
    distance_km: float = 0.0
    co2_emissions: float = 0.0
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    source_key: Optional[str] = None
    source_name: Optional[str] = None


class JourneyDetail(JourneySummary):
    source_type: Optional[str] = None
    source_provider: Optional[str] = None
    source_license: Optional[str] = None
    created_at: Optional[datetime] = None
