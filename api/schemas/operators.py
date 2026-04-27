from pydantic import BaseModel


class OperatorResponse(BaseModel):
    operator_id: int
    operator_name: str


class OperatorStatsResponse(BaseModel):
    operator_id: int
    operator_name: str
    total_trains: int
    countries_served: list[str]
    countries_count: int
