from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette import status

from cloud.app.services.operations.territory_service import TerritoryService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/api/v1/territories", tags=["territories"])


class CreateTerritoryRequest(BaseModel):
    name: str
    region: str
    provinces: list[str]
    hospitals: list[str]


class AssignRepRequest(BaseModel):
    rep_id: int


class SetTargetsRequest(BaseModel):
    monthly_visits: int
    quarterly_targets: dict


class OptimizeRouteRequest(BaseModel):
    start_location: str


@router.post("/create")
def create_territory(
    body: CreateTerritoryRequest,
    _: dict = Depends(require_scope("pharma")),
    service: TerritoryService = Depends(),
) -> Any:
    result = service.create_territory(
        name=body.name,
        region=body.region,
        provinces=body.provinces,
        hospitals=body.hospitals,
    )
    return success(data=result)


@router.post("/{territory_id}/assign-rep")
def assign_rep(
    territory_id: int,
    body: AssignRepRequest,
    _: dict = Depends(require_scope("pharma")),
    service: TerritoryService = Depends(),
) -> Any:
    try:
        result = service.assign_rep(territory_id, body.rep_id)
    except ValueError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    return success(data=result)


@router.post("/{territory_id}/targets")
def set_targets(
    territory_id: int,
    body: SetTargetsRequest,
    _: dict = Depends(require_scope("pharma")),
    service: TerritoryService = Depends(),
) -> Any:
    try:
        result = service.set_targets(territory_id, body.monthly_visits, body.quarterly_targets)
    except ValueError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    return success(data=result)


@router.get("/{territory_id}/progress")
def get_progress(
    territory_id: int,
    _: dict = Depends(require_scope("pharma")),
    service: TerritoryService = Depends(),
) -> Any:
    try:
        result = service.get_progress(territory_id)
    except ValueError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    return success(data=result)


@router.post("/{territory_id}/optimize-route")
def optimize_route(
    territory_id: int,
    body: OptimizeRouteRequest,
    _: dict = Depends(require_scope("pharma")),
    service: TerritoryService = Depends(),
) -> Any:
    try:
        result = service.optimize_route(territory_id, body.start_location)
    except ValueError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    return success(data=result)
