import json
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from starlette import status
from cloud.app.database import get_db
from cloud.app.repositories import (
    AgentPipelinesRepository, PipelineStepsRepository,
    PipelineRunsRepository, PipelineStepRunsRepository,
)
from shared.auth_scope import require_scope
from shared.base import success, PaginatedResponse

router = APIRouter(prefix="/agent/pipelines", tags=["Agent系统"])


class StepDef(BaseModel):
    step_order: int
    agent_role_id: int
    input_mapping: dict = {}
    custom_prompt_override: str = ""


class PipelineCreate(BaseModel):
    name: str
    description: str = ""
    steps: list[StepDef]


class PipelineRunRequest(BaseModel):
    user_input: str = ""


def pd(row) -> dict:
    return {"id": row["id"], "name": row["name"], "description": row["description"],
            "is_active": row["is_active"], "created_by": row["created_by"],
            "created_at": row["created_at"], "updated_at": row["updated_at"]}


def sd(row) -> dict:
    return {"id": row["id"], "pipeline_id": row["pipeline_id"],
            "step_order": row["step_order"], "agent_role_id": row["agent_role_id"],
            "input_mapping": row["input_mapping"],
            "custom_prompt_override": row["custom_prompt_override"],
            "created_at": row["created_at"]}


def _p404(pipelines_repo, pid):
    row = pipelines_repo.get_by_id(pid)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    return row


@router.post("", status_code=status.HTTP_201_CREATED)
def create_pipeline(body: PipelineCreate,
                    current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    uid = int(current_user["sub"])
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pipelines_repo = AgentPipelinesRepository(db)
    steps_repo = PipelineStepsRepository(db)
    pid = pipelines_repo.create({
        "name": body.name, "description": body.description,
        "created_by": uid, "created_at": now, "updated_at": now,
    })
    for s in body.steps:
        steps_repo.create({
            "pipeline_id": pid, "step_order": s.step_order,
            "agent_role_id": s.agent_role_id,
            "input_mapping": json.dumps(s.input_mapping, ensure_ascii=False),
            "custom_prompt_override": s.custom_prompt_override,
        })
    return success(data=pd(pipelines_repo.get_by_id(pid)))


@router.get("")
def list_pipelines(current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    pipelines_repo = AgentPipelinesRepository(db)
    steps_repo = PipelineStepsRepository(db)
    rows = pipelines_repo.list_all(order_by="created_at DESC")
    result = []
    for r in rows:
        step_count = steps_repo.count(conditions=["pipeline_id=?"], params=[r["id"]])
        result.append({**pd(r), "step_count": step_count})
    return success(data=result)


# IMPORTANT: /runs/{run_id} MUST come before /{pipeline_id} to avoid route conflicts
@router.get("/runs/{run_id}")
def get_run(run_id: int, current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    runs_repo = PipelineRunsRepository(db)
    step_runs_repo = PipelineStepRunsRepository(db)
    row = runs_repo.get_by_id(run_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Run not found")
    steps = step_runs_repo.list_all(
        conditions=["run_id=?"], params=[run_id], order_by="step_order ASC"
    )
    return success(data={
        "run": dict(row),
        "step_runs": steps,
    })


@router.get("/{pipeline_id}")
def get_pipeline(pipeline_id: int,
                 current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    pipelines_repo = AgentPipelinesRepository(db)
    steps_repo = PipelineStepsRepository(db)
    row = _p404(pipelines_repo, pipeline_id)
    steps = steps_repo.list_all(
        conditions=["pipeline_id=?"], params=[pipeline_id], order_by="step_order ASC"
    )
    return success(data={**pd(row), "steps": [sd(s) for s in steps]})


@router.delete("/{pipeline_id}")
def delete_pipeline(pipeline_id: int,
                    current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    pipelines_repo = AgentPipelinesRepository(db)
    steps_repo = PipelineStepsRepository(db)
    runs_repo = PipelineRunsRepository(db)
    _p404(pipelines_repo, pipeline_id)
    for step in steps_repo.list_all(conditions=["pipeline_id=?"], params=[pipeline_id]):
        steps_repo.delete(step["id"])
    for run in runs_repo.list_all(conditions=["pipeline_id=?"], params=[pipeline_id]):
        runs_repo.delete(run["id"])
    pipelines_repo.delete(pipeline_id)
    return success()


@router.post("/{pipeline_id}/run")
def run_pipeline(pipeline_id: int, body: PipelineRunRequest, request: Request,
                 current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    pipelines_repo = AgentPipelinesRepository(db)
    steps_repo = PipelineStepsRepository(db)
    runs_repo = PipelineRunsRepository(db)
    step_runs_repo = PipelineStepRunsRepository(db)

    pipeline = _p404(pipelines_repo, pipeline_id)
    steps = db.execute(
        "SELECT ps.*, ar.system_prompt, ar.name AS ar_name, ar.temperature, ar.max_tokens "
        "FROM pipeline_steps ps JOIN agent_roles ar ON ps.agent_role_id=ar.id "
        "WHERE ps.pipeline_id=? ORDER BY ps.step_order", (pipeline_id,)).fetchall()
    if not steps:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Pipeline has no steps")
    uid = int(current_user["sub"])
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_id = runs_repo.create({
        "pipeline_id": pipeline_id, "user_input": body.user_input,
        "status": "running", "started_at": now, "created_by": uid,
    })

    auth_header = request.headers.get("Authorization", "")
    previous_output = ""
    final_status = "completed"
    step_results = []

    for step in steps:
        s_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        input_mapping = json.loads(step["input_mapping"]) if step["input_mapping"] else {}
        user_content = body.user_input
        if input_mapping.get("user_input") == "$request":
            user_content = body.user_input
        ctx = input_mapping.get("context", "")
        strategy = input_mapping.get("strategy", "")
        if previous_output:
            if ctx == "previous_output":
                user_content = previous_output
            if strategy == "previous_output":
                user_content = previous_output
            if not input_mapping:
                user_content = previous_output

        messages = [
            {"role": "system", "content": step["custom_prompt_override"] or step["system_prompt"]},
            {"role": "user", "content": user_content},
        ]
        sr_id = step_runs_repo.create({
            "run_id": run_id, "step_order": step["step_order"],
            "agent_role_id": step["agent_role_id"], "agent_role_name": step["ar_name"],
            "input_data": json.dumps(messages, ensure_ascii=False),
            "status": "running", "started_at": s_now,
        })

        step_status = "completed"
        output_data = ""
        ai_raw = ""
        tokens = 0
        try:
            payload = {
                "messages": messages,
                "temperature": step["temperature"] or 0.7,
                "max_tokens": step["max_tokens"] or 2048,
            }
            req = urllib.request.Request(
                "http://localhost:8000/ai/chat",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "Authorization": auth_header},
                method="POST")
            with urllib.request.urlopen(req, timeout=120) as rp:
                resp = json.loads(rp.read().decode("utf-8"))
                ai_raw = resp.get("data", {}).get("reply", "")
                usage = resp.get("data", {}).get("usage", {})
                tokens = usage.get("total_tokens", 0) if usage else 0
                output_data = ai_raw
        except Exception as e:
            step_status = "failed"
            output_data = str(e)
            final_status = "failed"

        c_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        step_runs_repo.update(sr_id, {
            "output_data": output_data, "ai_response_raw": ai_raw,
            "tokens_used": tokens, "status": step_status, "completed_at": c_now,
        })
        step_results.append({
            "step_order": step["step_order"], "agent_name": step["ar_name"],
            "output": output_data, "status": step_status,
        })
        previous_output = output_data
        if step_status == "failed":
            break

    c_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    runs_repo.update(run_id, {
        "status": final_status,
        "result": json.dumps({"steps": step_results}, ensure_ascii=False),
        "completed_at": c_now,
    })
    return success(data={"run_id": run_id, "status": final_status, "steps": step_results})


@router.get("/{pipeline_id}/runs")
def list_runs(pipeline_id: int,
              page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
              current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    pipelines_repo = AgentPipelinesRepository(db)
    runs_repo = PipelineRunsRepository(db)
    _p404(pipelines_repo, pipeline_id)
    total, total_pages, rows = runs_repo.paginate(
        page=page, page_size=page_size,
        conditions=["pipeline_id=?"], params=[pipeline_id],
        order_by="started_at DESC",
    )
    return success(data=PaginatedResponse(
        items=rows, total=total, page=page,
        page_size=page_size, total_pages=total_pages,
    ))
