"""医保目录查询路由。"""

from fastapi import APIRouter, Query
from market_access.app.services.formulary_service import (
    get_formulary_status,
    get_reimbursement_info,
)

from shared.base import success

router = APIRouter(prefix="/api/formulary", tags=["医保目录"])


@router.get("/search")
async def formulary_search(
    drug_name: str = Query(..., description="药品名称"),
):
    """查询药品是否在医保目录内。返回目录状态、报销比例及限制条件。"""
    result = await get_formulary_status(drug_name)
    return success(data=result)


@router.get("/reimbursement")
async def reimbursement_info(
    drug_name: str = Query(..., description="药品名称"),
):
    """获取药品报销详细信息。返回报销比例、限制条件等。"""
    result = await get_reimbursement_info(drug_name)
    return success(data=result)
