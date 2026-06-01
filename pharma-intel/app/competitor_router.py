from fastapi import APIRouter, Query
from pharma_intel.app.services.competitor_service import (
    get_competitor_intel,
    get_market_news,
)
from shared.base import success

router = APIRouter(prefix="/api/competitor", tags=["竞品情报"])


@router.get("/intel")
async def competitor_intel(
    company: str = Query(..., description="公司名称"),
):
    """获取指定竞争对手的综合情报。返回新闻摘要、论文活动、近期事件。"""
    result = await get_competitor_intel(company)
    return success(data=result)


@router.get("/news")
async def market_news(
    limit: int = Query(10, ge=1, le=50),
):
    """获取行业新闻动态。返回最新行业新闻列表。"""
    result = await get_market_news(limit)
    return success(data=result)
