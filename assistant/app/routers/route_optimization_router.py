"""Multi-site route optimization APIs."""

from fastapi import APIRouter

from assistant.app.schemas.route_optimization import RouteRequest, RouteResult
from assistant.app.services.route_optimization_service import get_history, optimize_route

router = APIRouter(prefix="/api/route", tags=["路径优化"])


@router.post("/optimize", response_model=RouteResult, tags=["路径优化"])
def optimize(body: RouteRequest) -> RouteResult:
    return optimize_route(body.start_address, body.stops)


@router.get("/history/{rep_id}", response_model=list[RouteResult], tags=["路径优化"])
def history(rep_id: str) -> list[RouteResult]:
    return get_history(rep_id)
