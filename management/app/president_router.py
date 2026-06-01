from fastapi import APIRouter

from management.app.services.president_service import (
    get_compliance_overview,
    get_summary,
    get_team_rankings,
    get_trend_report,
)
from shared.base import success

router = APIRouter(prefix="/api/president", tags=["总裁视图"])


@router.get("/summary")
async def summary():
    """全局概览：仪表盘分析 + 团队列表 + 合规统计。"""
    data = await get_summary()
    return success(data=data)


@router.get("/compliance-overview")
async def compliance_overview():
    """合规概览：合规执行统计。"""
    data = await get_compliance_overview()
    return success(data=data)


@router.get("/team-rankings")
async def team_rankings():
    """团队排名：基于业绩指标的团队排行。"""
    data = await get_team_rankings()
    return success(data=data)


@router.get("/trend-report")
async def trend_report():
    """趋势报告：全局分析趋势数据。"""
    data = await get_trend_report()
    return success(data=data)
