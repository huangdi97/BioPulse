"""监察报告路由。"""

from fastapi import APIRouter, Query
from clinical_ops.app.services.monitoring_service import (
    get_monitoring_plan,
    get_monitoring_report,
    generate_report,
)
from shared.base import success

router = APIRouter(prefix="/api/monitoring", tags=["监察报告"])


@router.get("/plan")
async def plan(
    trial_id: str = Query(..., description="临床试验编号"),
):
    """获取临床试验监察计划。包括监察频率、范围和负责人。"""
    result = await get_monitoring_plan(trial_id)
    return success(data=result)


@router.get("/report")
async def report(
    trial_id: str = Query(..., description="临床试验编号"),
    report_id: str = Query(..., description="监察报告编号"),
):
    """获取指定监察报告详情。返回发现项和建议。"""
    result = await get_monitoring_report(trial_id, report_id)
    return success(data=result)


@router.post("/generate")
async def generate(
    trial_id: str = Query(..., description="临床试验编号"),
):
    """生成临床试验监察报告。基于试验当前数据自动生成。"""
    result = await generate_report(trial_id)
    return success(data=result)
