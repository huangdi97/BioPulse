from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from shared.auth import get_current_user
from shared.auth_scope import require_scope
from cloud.app.services.quotation_workflow_service import (
    submit_for_approval,
    approve,
    reject,
)

router = APIRouter(
    prefix="/api/research/quotations",
    tags=["科研线"],
    dependencies=[Depends(require_scope("research"))],
)


class RejectRequest(BaseModel):
    reason: str


@router.post("/{id}/submit")
def submit_quotation(id: int, current_user: dict = Depends(get_current_user)):
    try:
        submit_for_approval(id, current_user.get("username", "unknown"))
        return {"code": 0, "message": "submitted for approval"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{id}/approve")
def approve_quotation(id: int, current_user: dict = Depends(get_current_user)):
    try:
        approve(id, current_user.get("username", "unknown"))
        return {"code": 0, "message": "approved"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{id}/reject")
def reject_quotation(id: int, body: RejectRequest, current_user: dict = Depends(get_current_user)):
    try:
        reject(id, current_user.get("username", "unknown"), body.reason)
        return {"code": 0, "message": "rejected"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
