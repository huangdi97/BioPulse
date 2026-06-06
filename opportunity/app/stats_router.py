"""统计报表 API。"""

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from opportunity.app.services.stats_service import StatsService
from shared.auth_scope import require_scope
from shared.base import ApiResponse, success

router = APIRouter(prefix="", tags=["Opportunity Stats"])


class StageStat(BaseModel):
    count: int
    value: float


class ProductStat(BaseModel):
    product: str
    count: int
    value: float


class StatsData(BaseModel):
    total_count: int
    total_value: float
    by_stage: dict[str, StageStat]
    by_product: list[ProductStat]
    avg_value: float
    win_rate: float


@router.get("/stats", summary="通用统计", description="获取通用统计数据的占位接口")
def get_stats() -> ApiResponse:
    from fastapi.responses import JSONResponse

    return JSONResponse(
        content=success(data=[]).model_dump(),
        status_code=200,
    )


@router.get("/opportunities/stats", summary="商机统计", description="获取商机模块的聚合统计数据", response_model=ApiResponse[StatsData])
def get_opportunity_stats(
    start_date: str | None = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="结束日期 (YYYY-MM-DD)"),
    service: StatsService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> Any:
    """获取opportunity stats。"""
    data = service.get_stats(start_date, end_date)

    by_stage = {stage: StageStat(count=s["count"], value=s["value"]) for stage, s in data["by_stage"].items()}
    by_product = [ProductStat(product=p["product"], count=p["count"], value=p["value"]) for p in data["by_product"]]

    return success(
        data=StatsData(
            total_count=data["total_count"],
            total_value=data["total_value"],
            by_stage=by_stage,
            by_product=by_product,
            avg_value=data["avg_value"],
            win_rate=data["win_rate"],
        )
    )
