"""Route optimization schemas."""

from pydantic import BaseModel, Field


class RouteStop(BaseModel):
    address: str
    lat: float
    lng: float
    priority: int = Field(default=5, ge=0, le=10)
    time_window: str | None = None


class RouteRequest(BaseModel):
    start_address: str
    stops: list[RouteStop] = Field(default_factory=list)


class RouteResult(BaseModel):
    optimized_order: list[RouteStop] = Field(default_factory=list)
    total_distance_km: float
    total_duration_min: int
