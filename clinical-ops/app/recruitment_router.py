"""患者招募路由。"""

from fastapi import APIRouter, Query
from clinical_ops.app.services.recruitment_service import get_recruitment_status, get_pipeline
from shared.base import success

router = APIRouter(prefix="/api/recruitment", tags=["患者招募"])


@router.get("/status")
async def status(
    trial_id: str = Query(..., description="临床试验编号"),
):
    """查询临床试验招募进度。返回已入组数、目标数和完成百分比。"""
    result = await get_recruitment_status(trial_id)
    return success(data=result)


@router.get("/pipeline")
async def pipeline():
    """获取患者招募管线总览。汇总所有在研试验的招募进度和阶段分布。"""
    result = await get_pipeline()
    return success(data=result)
