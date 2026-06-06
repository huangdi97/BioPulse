"""经理视图路由。提供团队统计、成员列表、合规和绩效数据查询。"""

from fastapi import APIRouter, Path

from management.app.services.manager_service import (
    get_team_compliance,
    get_team_members,
    get_team_performance,
    get_team_stats,
)
from shared.base import success

router = APIRouter(prefix="/api/manager", tags=["经理视图"])


@router.get("/team/{team_id}/stats", summary="团队统计", description="获取指定团队的成员统计和看板聚合数据")
async def team_stats(team_id: int = Path(..., description="团队 ID")):
    """团队统计：成员列表 + 看板统计聚合。"""
    data = await get_team_stats(team_id)
    return success(data=data)


@router.get("/team/{team_id}/members", summary="成员列表", description="获取指定团队的成员列表信息")
async def team_members(team_id: int = Path(..., description="团队 ID")):
    """团队成员列表。"""
    data = await get_team_members(team_id)
    return success(data=data)


@router.get("/team/{team_id}/compliance", summary="团队合规", description="获取指定团队的合规执行数据")
async def team_compliance(team_id: int = Path(..., description="团队 ID")):
    """团队合规数据。"""
    data = await get_team_compliance(team_id)
    return success(data=data)


@router.get("/team/{team_id}/performance", summary="团队绩效", description="获取指定团队的绩效评估数据")
async def team_performance(team_id: int = Path(..., description="团队 ID")):
    """团队绩效数据。"""
    data = await get_team_performance(team_id)
    return success(data=data)
