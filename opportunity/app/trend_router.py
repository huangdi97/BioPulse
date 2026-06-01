from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from starlette import status

from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success
from opportunity.app.services.trend_service import TrendService

router = APIRouter(tags=["trends"])


class TrendPoint(BaseModel):
    period: str
    count: int


class TrendByTopicOut(BaseModel):
    topic: str
    period: str
    data_points: List[TrendPoint]
    total: int


class TrendPredictRequest(BaseModel):
    topic: str
    context: Optional[str] = None


class TrendPredictOut(BaseModel):
    topic: str
    prediction: str
    confidence: str
    driving_factors: list
    similar_topics: list
    data_points_months: int


class TrendAnalysisOut(BaseModel):
    id: int
    topic: str
    analysis_type: str
    period: Optional[str] = None
    data_summary: Optional[str] = None
    result: Optional[str] = None
    confidence: str = "medium"
    analyzed_at: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[str] = None


@router.get("/trends/by-topic")
def trends_by_topic(
    topic: str = Query(..., description="Research topic"),
    period: str = Query("monthly", description="Aggregation period: monthly/quarterly/yearly"),
    service: TrendService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    data = service.get_trends_by_topic(topic, period)
    data_points = [TrendPoint(**p) for p in data["data_points"]]
    return success(data=TrendByTopicOut(
        topic=data["topic"], period=data["period"],
        data_points=data_points, total=data["total"],
    ))


@router.post("/trends/predict")
def trend_predict(
    body: TrendPredictRequest,
    request: Request,
    service: TrendService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    auth_header = request.headers.get("Authorization", "")
    user_id = int(current_user["sub"])
    result = service.predict_trend(body, auth_header, user_id)
    return success(data=TrendPredictOut(**result))


@router.get("/trends/history")
def trend_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: TrendService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse]:
    total, total_pages, rows = service.list_history(page, page_size)
    items = [TrendAnalysisOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items, total=total, page=page,
            page_size=page_size, total_pages=total_pages,
        )
    )
