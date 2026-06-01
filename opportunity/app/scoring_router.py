from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from starlette import status

from opportunity.app.services.scoring_service import ScoringService
from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success

router = APIRouter(prefix="/scoring", tags=["scoring"])


class ScoreUpdate(BaseModel):
    heat_score: int

    @field_validator("heat_score")
    @classmethod
    def validate_heat_score(cls, v: int) -> int:
        if v < 0 or v > 100:
            raise ValueError("heat_score must be between 0 and 100")
        return v


class ScoreLeaderboardItem(BaseModel):
    id: int
    name: str
    hcp_name: Optional[str] = None
    hospital: Optional[str] = None
    product: Optional[str] = None
    estimated_value: Optional[float] = None
    stage: Optional[str] = None
    probability: Optional[int] = None
    heat_score: int
    updated_at: Optional[str] = None


class RecalculateOut(BaseModel):
    total_updated: int
    average_score: float
    top_score: int
    bottom_score: int


@router.get("/leaderboard")
def leaderboard(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    stage: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None),
    max_score: Optional[int] = Query(None),
    service: ScoringService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[ScoreLeaderboardItem]]:
    total, total_pages, rows = service.leaderboard(
        page=page,
        page_size=page_size,
        stage=stage,
        min_score=min_score,
        max_score=max_score,
    )
    items = [ScoreLeaderboardItem(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.patch("/{opportunity_id}")
def set_heat_score(
    opportunity_id: int,
    body: ScoreUpdate,
    service: ScoringService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    updated = service.set_heat_score(opportunity_id, body.heat_score)
    return JSONResponse(
        content=success(data=updated).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@router.post("/recalculate")
def recalculate(
    service: ScoringService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[RecalculateOut]:
    result = service.recalculate()
    return success(data=RecalculateOut(**result))
