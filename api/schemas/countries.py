from pydantic import BaseModel


class CountryResponse(BaseModel):
    country_id: int
    country_code: str
    country_name: str


class CountryStatsResponse(BaseModel):
    stats_id: int
    passengers: float
    co2_emissions: float
    co2_per_passenger: float
    country_name: str
    country_code: str
    year: int
