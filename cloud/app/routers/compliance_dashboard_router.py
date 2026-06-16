"""合规仪表板路由：合规摘要与代表违规查询。"""

from fastapi import APIRouter, Depends

from cloud.app.compliance.service import ComplianceService
from shared.auth import get_current_user
from shared.base import success

router = APIRouter(prefix="/api/compliance/dashboard", tags=["合规"])


@router.get("/summary", summary="合规摘要", description="获取合规仪表盘的概要数据", tags=["合规"])
def dashboard_summary(
    current_user: dict = Depends(get_current_user),
    service: ComplianceService = Depends(),
):
    return success(data=service.dashboard_summary())


@router.get("/reps/{rep_id}", summary="代表违规查询", description="查询指定代表的违规记录", tags=["合规"])
def rep_violations(
    rep_id: int,
    current_user: dict = Depends(get_current_user),
    service: ComplianceService = Depends(),
):
    return success(data=service.rep_violations(rep_id))
