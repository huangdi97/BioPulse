"""Agent 异步任务路由 + HITL 审批端点。"""

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel

from cloud.app.agent_runtime.middleware.hitl import (
    check_approval_timeouts,
    get_pending_approvals,
    resolve_approval,
)
from cloud.app.agent_runtime.task_queue import get_task_queue
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/api/v1/agent/tasks", tags=["Agent 任务队列"])


class TaskSubmitRequest(BaseModel):
    agent_key: str
    goal: str
    context: dict | None = None


class ApproveRequest(BaseModel):
    approver: str
    resolution: str


@router.post("")
def submit_task(
    body: TaskSubmitRequest,
    user=Depends(require_scope("visit")),
):
    queue = get_task_queue()
    task_id = queue.submit(body.goal, body.agent_key, body.context)
    return success(data={"task_id": task_id, "status": "pending"})


@router.get("/{task_id}")
def get_task(
    task_id: str = Path(..., description="任务 ID"),
    user=Depends(require_scope("visit")),
):
    queue = get_task_queue()
    result = queue.get_result(task_id)
    if result is None:
        from fastapi import HTTPException
        from starlette import status

        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    return success(data=result)


@router.get("")
def list_tasks(
    limit: int = Query(20, ge=1, le=100),
    user=Depends(require_scope("visit")),
):
    queue = get_task_queue()
    return success(data={"items": queue.list_tasks(limit=limit)})


@router.get("/approvals/pending")
def list_pending_approvals(
    user=Depends(require_scope("approve")),
):
    items = get_pending_approvals()
    return success(data={"items": items})


@router.post("/approvals/{approval_id}/resolve")
def approve_request(
    approval_id: str = Path(..., description="审批工单 ID"),
    body: ApproveRequest = None,
    user=Depends(require_scope("approve")),
):
    ok = resolve_approval(approval_id, body.approver, body.resolution)
    if not ok:
        from fastapi import HTTPException
        from starlette import status

        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Approval not found or already resolved")
    return success(data={"approval_id": approval_id, "resolution": body.resolution})


@router.post("/approvals/check-timeouts")
def check_timeouts(
    user=Depends(require_scope("approve")),
):
    escalated = check_approval_timeouts()
    return success(data={"escalated_count": len(escalated), "escalated_ids": escalated})
