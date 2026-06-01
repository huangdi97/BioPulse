from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from starlette import status
from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success
from assistant.app.services.health_radar_service import HealthRadarService

router = APIRouter(prefix="/health-radar", tags=["health-radar"])


class HealthRadarCreate(BaseModel):
    patient_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    diagnosis: Optional[str] = None
    risk_factors: Optional[str] = None
    medication_history: Optional[str] = None
    score: Optional[int] = 50
    assessment_date: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("score")
    @classmethod
    def score_range(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 0 or v > 100):
            raise ValueError("score must be between 0 and 100")
        return v


class HealthRadarUpdate(BaseModel):
    patient_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    diagnosis: Optional[str] = None
    risk_factors: Optional[str] = None
    medication_history: Optional[str] = None
    score: Optional[int] = None
    assessment_date: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[int] = None

    @field_validator("score")
    @classmethod
    def score_range(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 0 or v > 100):
            raise ValueError("score must be between 0 and 100")
        return v


class HealthRadarOut(BaseModel):
    id: int
    patient_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    diagnosis: Optional[str] = None
    risk_factors: Optional[str] = None
    medication_history: Optional[str] = None
    score: int
    assessment_date: Optional[str] = None
    notes: Optional[str] = None
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("")
def create_health_radar(
    body: HealthRadarCreate,
    service: HealthRadarService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    user_id = int(current_user["sub"])
    result = service.create(body, user_id)
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("")
def list_health_radar(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    patient_name: Optional[str] = Query(None),
    score_min: Optional[int] = Query(None),
    score_max: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    service: HealthRadarService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[HealthRadarOut]]:
    total, total_pages, rows = service.list(
        page, page_size, patient_name, score_min, score_max, date_from, date_to
    )
    items = [HealthRadarOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/stats")
def get_health_radar_stats(
    service: HealthRadarService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict]:
    data = service.get_stats()
    return success(data=data)


@router.get("/{health_radar_id}")
def get_health_radar(
    health_radar_id: int,
    service: HealthRadarService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[HealthRadarOut]:
    row = service.get(health_radar_id)
    return success(data=HealthRadarOut(**row))


@router.patch("/{health_radar_id}")
def update_health_radar(
    health_radar_id: int,
    body: HealthRadarUpdate,
    service: HealthRadarService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[HealthRadarOut]:
    updated = service.update(health_radar_id, body)
    return success(data=HealthRadarOut(**updated))


@router.delete("/{health_radar_id}")
def delete_health_radar(
    health_radar_id: int,
    service: HealthRadarService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    service.delete(health_radar_id)
    return success(message="deleted")
