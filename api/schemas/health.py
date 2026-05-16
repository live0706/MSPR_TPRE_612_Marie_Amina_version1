from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class HealthComponent(BaseModel):
    status: Literal["ok", "degraded", "error"]
    detail: str


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "error"]
    environment: str
    version: str
    timestamp: datetime
    database: HealthComponent
    quality_report: HealthComponent
    model_metrics: HealthComponent


class MonitoringSummary(BaseModel):
    api_name: str
    api_version: str
    database_connected: bool
    prometheus_enabled: bool
    metrics_endpoint: str
    grafana_url: str
    prometheus_url: str
    total_trips: int
    total_countries: int
    total_operators: int
    latest_ingestion_at: datetime | None = None
