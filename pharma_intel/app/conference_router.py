"""学术会议追踪路由。提供即将召开的会议列表、会议详情和热点趋势分析。"""

from fastapi import APIRouter, HTTPException, Query
from starlette import status

from pharma_intel.app.services.conference_service import (
    analyze_conference_trends,
    get_conference_detail,
    get_upcoming_conferences,
)
from shared.base import success

router = APIRouter(prefix="/api/conference")


@router.get("/upcoming", tags=["情报源"])
async def upcoming_conferences(
    limit: int = Query(10, ge=1, le=50, description="返回会议数量上限"),
):
    """获取即将召开的学术会议列表。返回名称、日期、地点、热点话题、KOL等信息。"""
    result = await get_upcoming_conferences(limit)
    return success(data=result)


@router.get("/{conference_id}", tags=["情报源"])
async def conference_detail(
    conference_id: str,
):
    """获取指定会议的详细信息，包括议程、演讲嘉宾及相关论文。"""
    result = await get_conference_detail(conference_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conference '{conference_id}' not found",
        )
    return success(data=result)


@router.get("/trends", tags=["情报源"])
async def conference_trends(
    months: int = Query(6, ge=1, le=24, description="分析窗口月数"),
):
    """分析近期学术会议热点话题趋势。返回热门话题排名及覆盖会议数。"""
    result = await analyze_conference_trends(months)
    return success(data=result)
