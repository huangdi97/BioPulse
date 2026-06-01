"""随访管理路由。"""

from fastapi import APIRouter, Query
from patient_engage.app.services.followup_service import (
    create_followup_plan,
    get_followup_status,
    get_pending_followups,
)
from shared.base import success

router = APIRouter(prefix="/api/followup", tags=["随访管理"])


@router.post("/plan")
async def plan(body: dict):
    """创建随访计划。为患者制定随访频率和项目。"""
    result = await create_followup_plan(
        body.get("patient_id", ""),
        body.get("plan", {}),
    )
    return success(data=result)


@router.get("/status")
async def status(
    patient_id: str = Query(..., description="患者标识"),
):
    """随访状态。查询患者的随访进度和完成情况。"""
    result = await get_followup_status(patient_id)
    return success(data=result)


@router.get("/pending")
async def pending():
    """待随访列表。获取所有待完成的随访任务。"""
    result = await get_pending_followups()
    return success(data=result)
