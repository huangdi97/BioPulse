"""临床里程碑跟踪路由。"""

from fastapi import APIRouter, Query

from shared.base import success

from ..services.milestone_tracker_service import (
    get_gantt_data,
    get_site_progress,
    get_trial_timeline,
)

router = APIRouter(prefix="/api/milestone")


@router.get("/timeline", tags=["里程碑"])
async def timeline(
    trial_id: str = Query(..., description="试验编号"),
):
    """获取试验里程碑时间线。"""
    result = await get_trial_timeline(trial_id)
    return success(data=result)


@router.get("/site/{site_id}", tags=["里程碑"])
async def site_progress(site_id: str):
    """获取中心里程碑进度。"""
    result = await get_site_progress(site_id)
    return success(data=result)


@router.get("/gantt", tags=["里程碑"])
async def gantt(
    trial_id: str = Query(..., description="试验编号"),
):
    """获取 Gantt 图渲染数据。"""
    result = await get_gantt_data(trial_id)
    return success(data=result)
