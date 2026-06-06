"""用药提醒路由。"""

from fastapi import APIRouter, Query

from patient_engage.app.services.reminder_service import (
    create_reminder,
    get_adherence_report,
    get_reminder_status,
)
from shared.base import success

router = APIRouter(prefix="/api/reminder", tags=["用药提醒"])


@router.post("/create")
async def create(body: dict):
    """创建提醒计划。配置用药提醒的时间、频率和药品信息。"""
    result = await create_reminder(
        body.get("patient_id", ""),
        body.get("drug", ""),
        body.get("schedule", {}),
    )
    return success(data=result)


@router.get("/status")
async def status(
    patient_id: str = Query(..., description="患者标识"),
):
    """依从性状态。查询患者的用药提醒完成情况。"""
    result = await get_reminder_status(patient_id)
    return success(data=result)


@router.get("/adherence")
async def adherence(
    patient_id: str = Query(..., description="患者标识"),
    days: int = Query(30, description="报告天数"),
):
    """依从性报告。生成指定时间范围的依从性分析。"""
    result = await get_adherence_report(patient_id, days)
    return success(data=result)
