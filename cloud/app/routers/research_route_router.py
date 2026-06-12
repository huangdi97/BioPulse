from fastapi import APIRouter, Depends
from pydantic import BaseModel

from cloud.app.services.route_tsp import (
    estimate_travel_time,
    haversine,
    optimize_route,
)
from shared.auth import get_current_user
from shared.auth_scope import require_scope
from shared.base import success

route_router = APIRouter(
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


@route_router.post("/optimize", summary="路线优化", description="对多个科研路线点进行路径优化排序", tags=["Research"])
def post_optimize(
    body: OptimizeRequest,
    current_user: dict = Depends(get_current_user),
):
    points = [p.model_dump() for p in body.points]
    result = optimize_route(points)
    return {"code": 0, "data": result, "message": "success"}


@route_router.post("/estimate", summary="距离时间估算", description="估算两点之间的直线距离和预计行程时间", tags=["Research"])
def post_estimate(
    body: EstimateRequest,
    current_user: dict = Depends(get_current_user),
):
    distance = haversine(body.from_lat, body.from_lng, body.to_lat, body.to_lng)
    time_est = estimate_travel_time(distance)
    return success(
        data={
            "distance_km": round(distance, 2),
            "travel_time_hours": time_est,
        }
    )


__all__ = ["route_router", "EstimateRequest", "OptimizeRequest", "PointItem"]
