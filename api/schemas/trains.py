from typing import Optional

from pydantic import BaseModel


class TrainResponse(BaseModel):
    fact_id: int
    trip_id: str
    route_id: Optional[int] = None
    night_train: str
    country_name: str
    country_code: str
    operator_name: str
    year: int
    is_night: bool
    distance_km: float = 0.0
    co2_emissions: float = 0.0


class LegacyTrainSchema(BaseModel):
    trip_id: str
    operator_name: Optional[str] = None
    origin_city: Optional[str] = None
    destination_city: Optional[str] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    service_type: Optional[str] = None
    train_type: Optional[str] = None
    distance_km: Optional[float] = None
    co2_emissions: Optional[float] = 0.0
