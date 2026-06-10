from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from starlette import status
from cloud.app.services.admission_service import AdmissionService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/api/v1/admission", tags=["入院流程"])


class AdmissionCreate(BaseModel):
    hospital_name: str
    department: str = ""
    product: str
    status: str = "待提交"
    meeting_date: Optional[str] = None
    notes: str = ""
    rep_id: int = 0


class StatusUpdate(BaseModel):
    status: str


@router.post("", status_code=status.HTTP_201_CREATED, summary="创建入院记录", tags=["入院流程"])
def create(body: AdmissionCreate, _: dict = Depends(require_scope("visit")), service: AdmissionService = Depends()):
    result = service.create(body.model_dump())
    return success(data=result)


@router.get("", summary="入院列表", tags=["入院流程"])
def list_admissions(
    status: Optional[str] = Query(None),
    rep_id: Optional[int] = Query(None),
    service: AdmissionService = Depends(),
):
    result = service.list(status, rep_id)
    return success(data=result)


@router.get("/{record_id}", summary="入院详情", tags=["入院流程"])
def get_admission(record_id: int, service: AdmissionService = Depends()):
    result = service.get_by_id(record_id)
    if not result:
        raise HTTPException(404, "not found")
    return success(data=result)


@router.put("/{record_id}/status", summary="更新节点状态", tags=["入院流程"])
def update_status(record_id: int, body: StatusUpdate, _: dict = Depends(require_scope("visit")), service: AdmissionService = Depends()):
    result = service.update_status(record_id, body.status)
    if not result:
        raise HTTPException(404, "not found or invalid status")
    return success(data=result)
