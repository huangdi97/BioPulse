"""Agent 任务执行与提交路由。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from starlette import status

from cloud.app.services.agent_execution_service import AgentExecutionService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/agent/exec", tags=["Agent系统"])


class TaskSubmit(BaseModel):
    agent_role: str = ""
    action_type: str = "process"
    input_data: dict = {}
    max_retries: int = 3


class A2ATask(BaseModel):
    task_id: str = ""
    agent_role: str = ""
    input_data: dict = {}
    callback_url: str = ""


@router.post("/submit", status_code=status.HTTP_201_CREATED, tags=["Agent系统"])
def submit_task(body: TaskSubmit, current_user=Depends(require_scope("visit"))):
    svc = AgentExecutionService()
    return success(data=svc.submit_task(body, current_user))


@router.get("/tasks/list", tags=["Agent系统"])
def list_tasks(
    status_filter: Optional[str] = Query(None, alias="status"),
    agent_role: Optional[str] = Query(None),
    current_user=Depends(require_scope("visit")),
):
    svc = AgentExecutionService()
    return success(data=svc.list_tasks(status_filter, agent_role))


@router.get("/tasks/{task_id}", tags=["Agent系统"])
def get_task(task_id: str, current_user=Depends(require_scope("visit"))):
    svc = AgentExecutionService()
    return success(data=svc.get_task(task_id))


@router.post("/tasks/{task_id}/retry", tags=["Agent系统"])
def retry_task(task_id: str, current_user=Depends(require_scope("visit"))):
    svc = AgentExecutionService()
    return success(data=svc.retry_task(task_id))


@router.post("/tasks/{task_id}/approve", tags=["Agent系统"])
def approve_task(task_id: str, current_user=Depends(require_scope("visit"))):
    svc = AgentExecutionService()
    return success(data=svc.approve_task(task_id))


@router.get("/a2a/card", tags=["Agent系统"])
def a2a_card(current_user=Depends(require_scope("visit"))):
    svc = AgentExecutionService()
    return success(data=svc.a2a_card())


@router.post("/a2a/task", status_code=status.HTTP_201_CREATED, tags=["Agent系统"])
def a2a_task(body: A2ATask, current_user=Depends(require_scope("visit"))):
    svc = AgentExecutionService()
    return success(data=svc.a2a_task(body))
