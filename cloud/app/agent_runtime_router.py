"""Agent 运行时执行路由。"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from cloud.app.agent_database import get_agent_db
from cloud.app.agent_runtime.agent_specs import AGENT_SPECS
from cloud.app.agent_runtime.runtime_core import AgentRuntime
from cloud.app.agent_runtime.tool_bridge import ToolRegistry
from cloud.app.database import get_db
from cloud.app.services.agent_runtime_service import AgentRuntimeService
from shared.auth_scope import require_scope

router = APIRouter(prefix="/agent/runtime", tags=["Agent Runtime"])


class ExecuteRequest(BaseModel):
    agent_key: str
    goal: str
    context: dict | None = None


class TriggerRequest(BaseModel):
    goal: str | None = None


def _auth_header(request: Request) -> str:
    return request.headers.get("Authorization", "")


@router.post("/execute")
def execute(
    body: ExecuteRequest,
    request: Request,
    agent_db=Depends(get_agent_db),
    business_db=Depends(get_db),
    user=Depends(require_scope("visit")),
):
    runtime = AgentRuntime(agent_db, business_db, request.headers.get("Authorization", ""))
    result = runtime.execute(body.goal, body.agent_key, body.context)
    return result.model_dump()


@router.get("/status")
def get_status(
    user=Depends(require_scope("visit")),
    service: AgentRuntimeService = Depends(),
):
    return service.get_status()


@router.get("/logs")
def get_logs(
    agent_key: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user=Depends(require_scope("visit")),
    service: AgentRuntimeService = Depends(),
):
    return service.get_logs(agent_key, status, page, page_size)


@router.post("/trigger/{agent_key}")
def trigger_agent(
    agent_key: str,
    request: Request,
    body: TriggerRequest = TriggerRequest(),
    agent_db=Depends(get_agent_db),
    business_db=Depends(get_db),
    user=Depends(require_scope("visit")),
):
    spec = AGENT_SPECS.get(agent_key)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"unknown agent_key: {agent_key}")

    goal = body.goal or spec["role_desc"]
    runtime = AgentRuntime(agent_db, business_db, request.headers.get("Authorization", ""))
    result = runtime.execute(goal, agent_key)
    return result.model_dump()


@router.get("/tools")
def list_tools(
    user=Depends(require_scope("visit")),
):
    registry = ToolRegistry()
    registry.register_default_tools()
    return registry.list_tools()


@router.get("/approvals/pending")
def list_pending_approvals(
    user=Depends(require_scope("visit")),
    service: AgentRuntimeService = Depends(),
):
    return {"items": service.list_pending_approvals()}


@router.post("/approvals/{approval_id}/approve")
def approve_approval(
    approval_id: int,
    user=Depends(require_scope("visit")),
    service: AgentRuntimeService = Depends(),
):
    username = user.get("username", "unknown")
    service.approve_approval(approval_id, username)
    return {"message": "approved", "approval_id": approval_id}


@router.post("/approvals/{approval_id}/reject")
def reject_approval(
    approval_id: int,
    user=Depends(require_scope("visit")),
    service: AgentRuntimeService = Depends(),
):
    username = user.get("username", "unknown")
    service.reject_approval(approval_id, username)
    return {"message": "rejected", "approval_id": approval_id}


@router.post("/resume")
def resume_execution(
    request: Request,
    agent_db=Depends(get_agent_db),
    business_db=Depends(get_db),
    user=Depends(require_scope("visit")),
):
    """恢复一个等待审批的 Agent 执行。"""
    runtime = AgentRuntime(agent_db, business_db, _auth_header(request))
    result = runtime.resume("", "")
    return result.model_dump()
