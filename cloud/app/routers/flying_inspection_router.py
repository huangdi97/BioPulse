"""飞检准备度仪表盘 API。"""

from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel
from starlette import status

from cloud.app.services.flying_inspection_service import (
    confirm_remediation,
    create_remediation_task,
    get_audit_trail,
    get_checklist,
    get_dashboard,
    get_history,
)

router = APIRouter(prefix="/api/inspection", tags=["飞检准备度"])


class RemediationTaskCreate(BaseModel):
    title: str
    description: str = ""
    assignee: str
    deadline: str
    inspection_id: str = "inspection-2026-06"
    who: str = "质量负责人"
    evidence: str = "remediation-task-form"


class RemediationConfirm(BaseModel):
    inspection_id: str = "inspection-2026-06"
    who: str = "质量负责人"
    evidence: str = "remediation-evidence"


@router.get("/dashboard", tags=["飞检准备度"])
def inspection_dashboard():
    return get_dashboard()


@router.get("/checklist", tags=["飞检准备度"])
def inspection_checklist(category: Optional[str] = Query(None, description="检查类别")):
    return get_checklist(category=category)


@router.post("/task", status_code=status.HTTP_201_CREATED, tags=["飞检准备度"])
def inspection_task_create(body: RemediationTaskCreate):
    return create_remediation_task(
        title=body.title,
        description=body.description,
        assignee=body.assignee,
        deadline=body.deadline,
        inspection_id=body.inspection_id,
        who=body.who,
        evidence=body.evidence,
    )


@router.put("/task/{task_id}/confirm", tags=["飞检准备度"])
def inspection_task_confirm(task_id: str, body: RemediationConfirm | None = None):
    request = body or RemediationConfirm()
    return confirm_remediation(
        task_id,
        inspection_id=request.inspection_id,
        who=request.who,
        evidence=request.evidence,
    )


@router.get("/history", tags=["飞检准备度"])
def inspection_history():
    return get_history()


@router.get("/{inspection_id}/audit-trail", tags=["飞检准备度"])
def inspection_audit_trail(inspection_id: str):
    return get_audit_trail(inspection_id)
