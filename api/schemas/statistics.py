from pydantic import BaseModel


class DashboardMetricsResponse(BaseModel):
    country_name: str
    country_code: str
    avg_passengers: float
    avg_co2_emissions: float
    avg_co2_per_passenger: float


class KPIsResponse(BaseModel):
    total_countries: int
    total_trains: int
    total_operators: int
    years_covered: str
    avg_co2_per_passenger: float
    total_passengers: float
    total_co2_emissions: float


class TimelineData(BaseModel):
    year: int
    passengers: float
    co2_emissions: float
    co2_per_passenger: float
    train_count: int


class CO2RankingItem(BaseModel):
    country_name: str
    country_code: str
    avg_co2_per_passenger: float
    ranking: int
    performance: str


class TrainTypeComparison(BaseModel):
    train_type: str
    train_count: int
    avg_distance_km: float
    avg_co2_emissions: float
    efficiency_score: float
