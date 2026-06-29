from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from cloud.app.services.content.content_service import ContentService
from shared.auth_scope import require_scope

router = APIRouter(prefix="/api/v1/content", tags=["content"])

service = ContentService()


class UploadRequest(BaseModel):
    title: str
    type: str
    tags: list[str] = []
    hcp_target: bool = False
    expire_days: Optional[int] = None


class RejectRequest(BaseModel):
    reason: str = ""


class ClmViewRequest(BaseModel):
    representative: str
    hcp_id: str
    feedback: Optional[str] = None


@router.post("/upload")
def upload_content(body: UploadRequest, _=Depends(require_scope("pharma"))):
    result = service.upload_content(
        title=body.title,
        content_type=body.type,
        tags=body.tags,
        hcp_target=body.hcp_target,
        expire_days=body.expire_days,
    )
    return {"status": "ok", "content": result}


@router.post("/{content_id}/approve")
def approve_content(content_id: str, _=Depends(require_scope("pharma"))):
    result = service.approve_content(content_id)
    if not result:
        raise HTTPException(400, "Content not found or not in pending status")
    return {"status": "ok", "content": result}


@router.post("/{content_id}/reject")
def reject_content(content_id: str, body: RejectRequest = RejectRequest(), _=Depends(require_scope("pharma"))):
    result = service.reject_content(content_id, reason=body.reason)
    if not result:
        raise HTTPException(400, "Content not found or not in pending status")
    return {"status": "ok", "content": result}


@router.post("/clm/view")
def record_clm_view(body: ClmViewRequest, _=Depends(require_scope("pharma"))):
    result = service.record_clm_view(
        representative=body.representative,
        hcp_id=body.hcp_id,
        feedback=body.feedback,
    )
    return {"status": "ok", "log": result}


@router.get("/approved")
def list_approved(_=Depends(require_scope("pharma"))):
    items = service.list_approved()
    return {"status": "ok", "items": items}
