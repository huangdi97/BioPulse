from fastapi import APIRouter, Path
from management.app.services.manager_service import (
    get_team_stats,
    get_team_members,
    get_team_compliance,
    get_team_performance,
)
from shared.base import success

router = APIRouter(prefix="/api/manager", tags=["经理视图"])


@router.get("/team/{team_id}/stats")
async def team_stats(team_id: int = Path(..., description="团队 ID")):
    """团队统计：成员列表 + 看板统计聚合。"""
    data = await get_team_stats(team_id)
    return success(data=data)


@router.get("/team/{team_id}/members")
async def team_members(team_id: int = Path(..., description="团队 ID")):
    """团队成员列表。"""
    data = await get_team_members(team_id)
    return success(data=data)


@router.get("/team/{team_id}/compliance")
async def team_compliance(team_id: int = Path(..., description="团队 ID")):
    """团队合规数据。"""
    data = await get_team_compliance(team_id)
    return success(data=data)


@router.get("/team/{team_id}/performance")
async def team_performance(team_id: int = Path(..., description="团队 ID")):
    """团队绩效数据。"""
    data = await get_team_performance(team_id)
    return success(data=data)
