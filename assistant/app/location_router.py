from typing import List, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status

from assistant.app.services.location_service import LocationService
from shared.auth import get_current_user
from shared.base import ApiResponse, success

router = APIRouter(tags=["locations", "routes"])


class LocationCreate(BaseModel):
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_primary: Optional[int] = None
    notes: Optional[str] = None


class LocationUpdate(BaseModel):
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_primary: Optional[int] = None
    notes: Optional[str] = None


class LocationOut(BaseModel):
    id: int
    hcp_id: int
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_primary: int
    notes: Optional[str] = None
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RouteRequest(BaseModel):
    start_lat: float
    start_lng: float
    hcp_ids: List[int]
    max_results: Optional[int] = None


class RouteStop(BaseModel):
    hcp_id: int
    hcp_name: str
    address: str
    distance_km: float
    order: int


class RouteResponse(BaseModel):
    optimized_route: List[RouteStop]
    total_distance_km: float
    total_hcps: int


@router.post("/hcp/{hcp_id}/locations")
def create_location(
    hcp_id: int,
    body: LocationCreate,
    service: LocationService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    user_id = int(current_user["sub"])
    result = service.create(hcp_id, body, user_id)
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/hcp/{hcp_id}/locations")
def list_locations(
    hcp_id: int,
    service: LocationService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[List[LocationOut]]:
    rows = service.list(hcp_id)
    return success(data=[LocationOut(**r) for r in rows])


@router.patch("/locations/{location_id}")
def update_location(
    location_id: int,
    body: LocationUpdate,
    service: LocationService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[LocationOut]:
    updated = service.update(location_id, body)
    return success(data=LocationOut(**updated))


@router.delete("/locations/{location_id}")
def delete_location(
    location_id: int,
    service: LocationService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    service.delete(location_id)
    return success(message="deleted")


@router.post("/routes/optimize")
def optimize_route(
    body: RouteRequest,
    service: LocationService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[RouteResponse]:
    data = service.optimize_route(body)
    return success(
        data=RouteResponse(
            optimized_route=[RouteStop(**s) for s in data["optimized_route"]],
            total_distance_km=data["total_distance_km"],
            total_hcps=data["total_hcps"],
        )
    )
