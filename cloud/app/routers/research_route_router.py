from fastapi import APIRouter, Depends
from pydantic import BaseModel

from shared.auth import get_current_user
from shared.auth_scope import require_scope
from cloud.app.services.route_optimizer import (
    optimize_route,
    haversine,
    estimate_travel_time,
)

router = APIRouter(
    prefix="/api/research/route",
    tags=["research-route"],
    dependencies=[Depends(require_scope("research"))],
)


class PointItem(BaseModel):
    pi_id: int
    name: str
    lat: float
    lng: float
    priority: str = "normal"


class OptimizeRequest(BaseModel):
    points: list[PointItem]


class EstimateRequest(BaseModel):
    from_lat: float
    from_lng: float
    to_lat: float
    to_lng: float


@router.post("/optimize")
def post_optimize(
    body: OptimizeRequest,
    current_user: dict = Depends(get_current_user),
):
    points = [p.model_dump() for p in body.points]
    result = optimize_route(points)
    return {"code": 0, "data": result, "message": "success"}


@router.post("/estimate")
def post_estimate(
    body: EstimateRequest,
    current_user: dict = Depends(get_current_user),
):
    distance = haversine(body.from_lat, body.from_lng, body.to_lat, body.to_lng)
    time_est = estimate_travel_time(distance)
    return {
        "code": 0,
        "data": {
            "distance_km": round(distance, 2),
            "travel_time_hours": time_est,
        },
        "message": "success",
    }
