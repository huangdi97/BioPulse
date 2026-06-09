"""患者微信小程序路由。"""

from fastapi import APIRouter, Query

from shared.base import success

from ..schemas.patient_compliance import CheckInRequest, ReminderCreateRequest
from ..services.patient_compliance_service import checkin, get_compliance_report, set_reminder

router = APIRouter(prefix="/api/patient")


@router.post("/reminder", tags=["患者小程序"])
async def create_patient_reminder(body: ReminderCreateRequest):
    """创建患者用药提醒。"""
    result = await set_reminder(
        body.patient_id,
        body.drug or body.drug_name or "",
        body.schedule,
        body.dosage,
    )
    return success(data=result)


@router.post("/checkin", tags=["患者小程序"])
async def patient_checkin(body: CheckInRequest):
    """患者用药打卡。"""
    result = await checkin(body.reminder_id, body.confirmed)
    return success(data=result)


@router.get("/compliance/{patient_id}", tags=["患者小程序"])
async def patient_compliance(
    patient_id: str,
    period: str = Query("7d", description="统计周期，例如 7d、4w、1m"),
):
    """查询患者依从性报告。"""
    result = await get_compliance_report(patient_id, period)
    return success(data=result)
