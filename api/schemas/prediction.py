from datetime import datetime

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    distance_km: float = Field(..., gt=0, examples=[604.0])
    operator_name: str = Field("unknown", min_length=1, examples=["SNCF"])
    service_type: str = Field("Jour", min_length=1, examples=["Nuit"])
    train_type: str = Field("Rail", min_length=1, examples=["Rail"])
    country: str = Field("unknown", min_length=1, examples=["FR"])
    source_origin: str = Field("unknown", min_length=1, examples=["manual"])
    departure_time: datetime | None = Field(None, examples=["2026-12-01T19:30:00"])
    arrival_time: datetime | None = Field(None, examples=["2026-12-02T07:10:00"])
    origin_lat: float | None = None
    origin_lon: float | None = None
    destination_lat: float | None = None
    destination_lon: float | None = None


class PredictionResponse(BaseModel):
    predicted_co2_emissions: float
    unit: str = "kgCO2e"
    model_name: str
    model_version: str
    request_id: str
