from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from cloud.app.agent_runtime.agent_specs import AGENT_SPECS
from cloud.app.agent_runtime.runtime_core import AgentRuntime
from cloud.app.agent_runtime.tool_bridge import ToolRegistry
from cloud.app.database import get_db
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
    db=Depends(get_db),
    user=Depends(require_scope("visit")),
):
    runtime = AgentRuntime(db, _auth_header(request))
    result = runtime.execute(body.goal, body.agent_key, body.context)
    return result.model_dump()


@router.get("/status")
def get_status(
    request: Request,
    db=Depends(get_db),
    user=Depends(require_scope("visit")),
):
    runtime = AgentRuntime(db, _auth_header(request))
    return runtime.get_status()


@router.get("/logs")
def get_logs(
    request: Request,
    agent_key: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
    user=Depends(require_scope("visit")),
):
    conditions = []
    params = []
    if agent_key:
        conditions.append("agent_key = ?")
        params.append(agent_key)
    if status:
        conditions.append("status = ?")
        params.append(status)

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    offset = (page - 1) * page_size

    count_cur = db.execute(f"SELECT COUNT(*) as cnt FROM agent_runtime_logs{where}", params)
    total = count_cur.fetchone()["cnt"]

    cur = db.execute(
        f"SELECT * FROM agent_runtime_logs{where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        params + [page_size, offset],
    )
    rows = [dict(r) for r in cur.fetchall()]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": rows,
    }


@router.post("/trigger/{agent_key}")
def trigger_agent(
    agent_key: str,
    request: Request,
    body: TriggerRequest = TriggerRequest(),
    db=Depends(get_db),
    user=Depends(require_scope("visit")),
):
    spec = AGENT_SPECS.get(agent_key)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"unknown agent_key: {agent_key}")

    goal = body.goal or spec["role_desc"]
    runtime = AgentRuntime(db, _auth_header(request))
    result = runtime.execute(goal, agent_key)
    return result.model_dump()


@router.get("/tools")
def list_tools(
    db=Depends(get_db),
    user=Depends(require_scope("visit")),
):
    registry = ToolRegistry(db)
    registry.register_default_tools()
    return registry.list_tools()


@router.get("/approvals/pending")
def list_pending_approvals(
    db=Depends(get_db),
    user=Depends(require_scope("visit")),
):
    rows = db.execute("SELECT * FROM agent_runtime_approvals WHERE status='pending' ORDER BY created_at ASC").fetchall()
    return {"items": [dict(r) for r in rows]}


@router.post("/approvals/{approval_id}/approve")
def approve_approval(
    approval_id: int,
    request: Request,
    db=Depends(get_db),
    user=Depends(require_scope("visit")),
):
    now = datetime.now().isoformat()
    username = user.get("username", "unknown")
    db.execute(
        "UPDATE agent_runtime_approvals SET status='approved', responded_at=?, responded_by=? WHERE id=? AND status='pending'",
        (now, username, approval_id),
    )
    db.commit()
    return {"message": "approved", "approval_id": approval_id}


@router.post("/approvals/{approval_id}/reject")
def reject_approval(
    approval_id: int,
    request: Request,
    db=Depends(get_db),
    user=Depends(require_scope("visit")),
):
    now = datetime.now().isoformat()
    username = user.get("username", "unknown")
    db.execute(
        "UPDATE agent_runtime_approvals SET status='rejected', responded_at=?, responded_by=? WHERE id=? AND status='pending'",
        (now, username, approval_id),
    )
    db.commit()
    return {"message": "rejected", "approval_id": approval_id}


@router.post("/resume")
def resume_execution(
    request: Request,
    db=Depends(get_db),
    user=Depends(require_scope("visit")),
):
    """恢复一个等待审批的 Agent 执行。"""
    runtime = AgentRuntime(db, _auth_header(request))
    result = runtime.resume("", "")
    return result.model_dump()
