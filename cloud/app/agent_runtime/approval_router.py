"""审批工作流路由 — 发起审批、审批通过/拒绝、查询待审批列表。"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from cloud.app.agent_runtime.approval_workflow import ApprovalWorkflow
from cloud.app.database import DB_PATH
from shared.auth_scope import require_scope
from shared.base import success


def route_for_approval(agent_name: str, content: dict, risk_level: str | None = None) -> str:
    if risk_level:
        return risk_level
    mapping = {
        "compliance": "high",
        "analysis": "medium",
        "suggestion": "low",
    }
    return mapping.get(agent_name, "low")


router = APIRouter(prefix="/agent/approvals", tags=["Agent Approvals"])


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _get_workflow(db=None) -> ApprovalWorkflow:
    return ApprovalWorkflow(db or _get_db())


class ApprovalRequestCreate(BaseModel):
    event_type: str
    agent_name: str
    detail: dict | None = None
    timeout_hours: int = 24


class ApprovalAction(BaseModel):
    approver: str
    reason: str = ""


class ApprovalResubmit(BaseModel):
    editor: str
    params: dict


@router.post("", tags=["Agent Approvals"])
def create_approval(body: ApprovalRequestCreate, user=Depends(require_scope("visit"))):
    conn = _get_db()
    try:
        workflow = _get_workflow(conn)
        request_id = workflow.request_approval(
            event_type=body.event_type,
            agent_name=body.agent_name,
            detail=body.detail or {},
            timeout_hours=body.timeout_hours,
        )
        return success(data={"request_id": request_id, "status": "pending"})
    finally:
        conn.close()


@router.post("/{request_id}/approve", tags=["Agent Approvals"])
def approve_request(request_id: str, body: ApprovalAction, user=Depends(require_scope("visit"))):
    conn = _get_db()
    try:
        workflow = _get_workflow(conn)
        ok = workflow.approve(request_id, body.approver)
        if not ok:
            raise HTTPException(status_code=404, detail="Approval request not found or already processed")
        return success(data={"request_id": request_id, "status": "approved"})
    finally:
        conn.close()


@router.post("/{request_id}/reject", tags=["Agent Approvals"])
def reject_request(request_id: str, body: ApprovalAction, user=Depends(require_scope("visit"))):
    conn = _get_db()
    try:
        workflow = _get_workflow(conn)
        ok = workflow.reject(request_id, body.approver, body.reason)
        if not ok:
            raise HTTPException(status_code=404, detail="Approval request not found or already processed")
        return success(data={"request_id": request_id, "status": "rejected"})
    finally:
        conn.close()


@router.put("/{request_id}/resubmit", tags=["Agent Approvals"])
def resubmit_approval(request_id: str, body: ApprovalResubmit, user=Depends(require_scope("visit"))):
    conn = _get_db()
    try:
        workflow = _get_workflow(conn)
        ok = workflow.begin_editing(request_id, body.editor) and workflow.resubmit(request_id, body.editor, body.params)
        if not ok:
            raise HTTPException(status_code=404, detail="Approval request not found or not in rejected state")
        return success(data={"request_id": request_id, "status": "resubmitted"})
    finally:
        conn.close()


@router.get("", tags=["Agent Approvals"])
def list_approvals(
    status: str | None = Query(None),
    user=Depends(require_scope("visit")),
):
    conn = _get_db()
    try:
        workflow = _get_workflow(conn)
        if status == "pending":
            items = workflow.get_pending_requests()
        else:
            items = [r.to_dict() for r in workflow._manager.get_pending_requests()]
        return success(data={"items": items})
    finally:
        conn.close()
