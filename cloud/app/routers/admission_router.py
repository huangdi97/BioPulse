from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from starlette import status

from cloud.app.services.bidding.admission_service import AdmissionService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/api/v1/admissions", tags=["入院流程"])


class AdmissionCreate(BaseModel):
    hcp_id: int = Field(..., description="医疗机构ID")
    product_id: int = Field(..., description="产品ID")


class AdvanceRequest(BaseModel):
    approver: str = Field(..., description="审批人")
    notes: str = Field("", description="备注")


@router.post("", status_code=status.HTTP_201_CREATED, summary="创建入院流程")
def create(
    body: AdmissionCreate,
    _: dict = Depends(require_scope("manager")),
    service: AdmissionService = Depends(),
):
    result = service.create(body.hcp_id, body.product_id)
    return success(data=result)


@router.get("", summary="入院流程列表")
def list_admissions(
    hcp_id: Optional[int] = Query(None),
    product_id: Optional[int] = Query(None),
    _: dict = Depends(require_scope("manager")),
    service: AdmissionService = Depends(),
):
    result = service.summary(hcp_id, product_id)
    return success(data=result)


@router.get("/{record_id}", summary="入院流程详情")
def get_admission(
    record_id: int,
    _: dict = Depends(require_scope("manager")),
    service: AdmissionService = Depends(),
):
    result = service.get_status(record_id)
    return success(data=result)


@router.patch("/{record_id}/advance", summary="推进入院流程状态")
def advance(
    record_id: int,
    body: AdvanceRequest,
    _: dict = Depends(require_scope("manager")),
    service: AdmissionService = Depends(),
):
    result = service.advance_status(record_id, body.approver, body.notes)
    return success(data=result)
