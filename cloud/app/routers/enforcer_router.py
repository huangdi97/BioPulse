"""合规执行器路由：拜访合规检查与规则列表。"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from cloud.app.services.enforcer_service import EnforcerService
from shared.auth import get_current_user

router = APIRouter(prefix="/api/compliance/enforce", tags=["合规"])


class VisitCheckRequest(BaseModel):
    """拜访检查请求体。"""

    visit_data: dict


@router.post("")
def enforce_visit(
    body: VisitCheckRequest,
    current_user: dict = Depends(get_current_user),
    service: EnforcerService = Depends(),
):
    return service.check_visit(body.visit_data)


@router.get("/rules")
def list_rules(
    current_user: dict = Depends(get_current_user),
    service: EnforcerService = Depends(),
):
    return service.list_rules()
