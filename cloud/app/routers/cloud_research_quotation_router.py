"""Consolidated research quotation router module."""

from fastapi import APIRouter

"""科研报价单路由：模板列表与报价单生成。"""

from typing import Optional

from fastapi import Depends, HTTPException
from pydantic import BaseModel
from starlette import status

from cloud.app.services.quotations_service import (
    QUOTATION_TEMPLATES,
    generate_quotation,
)
from cloud.app.services.research_service import ResearchService
from shared.auth import get_current_user
from shared.auth_scope import require_scope
from shared.base import success

quotation_router = APIRouter(
    prefix="/api/research/quotations",
    tags=["科研线"],
    dependencies=[Depends(require_scope("research"))],
)


class GenerateQuotationRequest(BaseModel):
    """报价单生成请求体。"""

    template_id: str
    items: list[dict]
    customer_info: Optional[dict] = None


@quotation_router.get("/templates", tags=["Research Quotation"])
def list_templates(
    current_user: dict = Depends(get_current_user),
):
    return success(data=list(QUOTATION_TEMPLATES.values()))


@quotation_router.post("/generate", tags=["Research Quotation"])
def create_quotation(
    body: GenerateQuotationRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        result = generate_quotation(body.template_id, body.items)
        if body.customer_info:
            result["customer_info"] = body.customer_info
        ResearchService().log_audit(
            event_type="create",
            entity_type="quotation",
            entity_id=0,
            new_value=str(result),
            operator=current_user.get("username", ""),
        )
        return success(data=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


"""科研报价审批流水线路由：提交、批准、驳回。"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from cloud.app.services.quotation_workflow_service import (
    approve,
    reject,
    submit_for_approval,
)
from shared.auth import get_current_user
from shared.auth_scope import require_scope

quotation_workflow_router = APIRouter(
    prefix="/api/research/quotations",
    tags=["科研线"],
    dependencies=[Depends(require_scope("research"))],
)


class RejectRequest(BaseModel):
    """驳回请求体。"""

    reason: str


@quotation_workflow_router.post("/{id}/submit", tags=["Research Quotation Workflow"])
def submit_quotation(id: int, current_user: dict = Depends(get_current_user)):
    try:
        submit_for_approval(id, current_user.get("username", "unknown"))
        return success(message="submitted for approval")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@quotation_workflow_router.post("/{id}/approve", tags=["Research Quotation Workflow"])
def approve_quotation(id: int, current_user: dict = Depends(get_current_user)):
    try:
        approve(id, current_user.get("username", "unknown"))
        return success(message="approved")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@quotation_workflow_router.post("/{id}/reject", tags=["Research Quotation Workflow"])
def reject_quotation(id: int, body: RejectRequest, current_user: dict = Depends(get_current_user)):
    try:
        reject(id, current_user.get("username", "unknown"), body.reason)
        return success(message="rejected")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


router = APIRouter()

router.include_router(quotation_router)

router.include_router(quotation_workflow_router)

__all__ = ["router", "quotation_router", "quotation_workflow_router"]
