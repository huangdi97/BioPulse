import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from starlette import status

from cloud.app.database import get_db
from cloud.app.repositories import (
    AgentPipelinesRepository,
    PipelineRunsRepository,
    PipelineStepRunsRepository,
    PipelineStepsRepository,
)
from cloud.langgraph.pipeline_graph import get_pipeline_graph
from shared.auth_scope import require_scope
from shared.base import PaginatedResponse, success

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
    """将pipeline行数据格式化为字典。Args: row (sqlite3.Row) 数据库行。Returns: dict 格式化后的管道字典"""
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "is_active": row["is_active"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def sd(row) -> dict:
    """将step行数据格式化为字典。Args: row (sqlite3.Row) 数据库行。Returns: dict 格式化后的步骤字典"""
    return {
        "id": row["id"],
        "pipeline_id": row["pipeline_id"],
        "step_order": row["step_order"],
        "agent_role_id": row["agent_role_id"],
        "input_mapping": row["input_mapping"],
        "custom_prompt_override": row["custom_prompt_override"],
        "created_at": row["created_at"],
    }


def _p404(pipelines_repo, pid):
    row = pipelines_repo.get_by_id(pid)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    return row


@router.post("", status_code=status.HTTP_201_CREATED)
def create_pipeline(
    body: PipelineCreate,
    current_user=Depends(require_scope("visit")),
    db=Depends(get_db),
):
    """创建包含步骤定义的管道。Args: body (PipelineCreate) 管道创建体; current_user 用户; db SQLite连接。Returns: dict 成功响应"""
    uid = int(current_user["sub"])
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pipelines_repo = AgentPipelinesRepository(db)
    steps_repo = PipelineStepsRepository(db)
    pid = pipelines_repo.create(
        {
            "name": body.name,
            "description": body.description,
            "created_by": uid,
            "created_at": now,
            "updated_at": now,
        }
    )
    for s in body.steps:
        steps_repo.create(
            {
                "pipeline_id": pid,
                "step_order": s.step_order,
                "agent_role_id": s.agent_role_id,
                "input_mapping": json.dumps(s.input_mapping, ensure_ascii=False),
                "custom_prompt_override": s.custom_prompt_override,
            }
        )
    return success(data=pd(pipelines_repo.get_by_id(pid)))


@router.get("")
def list_pipelines(current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    """获取所有管道列表（含步骤数）。Args: current_user 用户; db SQLite连接。Returns: dict 成功响应"""
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
    """获取指定运行ID的运行详情及步骤运行记录。Args: run_id (int) 运行ID; current_user 用户; db SQLite连接。Returns: dict 成功响应"""
    runs_repo = PipelineRunsRepository(db)
    step_runs_repo = PipelineStepRunsRepository(db)
    row = runs_repo.get_by_id(run_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Run not found")
    steps = step_runs_repo.list_all(conditions=["run_id=?"], params=[run_id], order_by="step_order ASC")
    return success(
        data={
            "run": dict(row),
            "step_runs": steps,
        }
    )


@router.get("/{pipeline_id}")
def get_pipeline(pipeline_id: int, current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    """获取管道详情及其所有步骤。Args: pipeline_id (int) 管道ID; current_user 用户; db SQLite连接。Returns: dict 成功响应"""
    pipelines_repo = AgentPipelinesRepository(db)
    steps_repo = PipelineStepsRepository(db)
    row = _p404(pipelines_repo, pipeline_id)
    steps = steps_repo.list_all(conditions=["pipeline_id=?"], params=[pipeline_id], order_by="step_order ASC")
    return success(data={**pd(row), "steps": [sd(s) for s in steps]})


@router.delete("/{pipeline_id}")
def delete_pipeline(pipeline_id: int, current_user=Depends(require_scope("visit")), db=Depends(get_db)):
    """删除管道及其关联的步骤和运行记录。Args: pipeline_id (int) 管道ID; current_user 用户; db SQLite连接。Returns: dict 成功响应"""
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
def run_pipeline(
    pipeline_id: int,
    body: PipelineRunRequest,
    request: Request,
    current_user=Depends(require_scope("visit")),
    db=Depends(get_db),
):
    """执行指定管道，遍历各步骤并记录运行结果。
    Args: pipeline_id (int) 管道ID; body (PipelineRunRequest) 运行请求; request (Request) HTTP请求; current_user 用户; db SQLite连接。
    Returns: dict 成功响应"""
    pipelines_repo = AgentPipelinesRepository(db)
    PipelineStepsRepository(db)
    runs_repo = PipelineRunsRepository(db)
    step_runs_repo = PipelineStepRunsRepository(db)

    _p404(pipelines_repo, pipeline_id)
    steps = db.execute(
        "SELECT ps.*, ar.system_prompt, ar.name AS ar_name, ar.temperature, ar.max_tokens "
        "FROM pipeline_steps ps JOIN agent_roles ar ON ps.agent_role_id=ar.id "
        "WHERE ps.pipeline_id=? ORDER BY ps.step_order",
        (pipeline_id,),
    ).fetchall()
    if not steps:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Pipeline has no steps")
    uid = int(current_user["sub"])
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_id = runs_repo.create(
        {
            "pipeline_id": pipeline_id,
            "user_input": body.user_input,
            "status": "running",
            "started_at": now,
            "created_by": uid,
        }
    )

    auth_header = request.headers.get("Authorization", "")
    graph_steps = []
    for step in steps:
        graph_steps.append(
            {
                "step_order": step["step_order"],
                "agent_role_id": step["agent_role_id"],
                "agent_name": step["ar_name"],
                "system_prompt": step["system_prompt"],
                "custom_prompt_override": step["custom_prompt_override"],
                "temperature": step["temperature"] or 0.7,
                "max_tokens": step["max_tokens"] or 2048,
                "input_mapping": json.loads(step["input_mapping"]) if step["input_mapping"] else {},
            }
        )

    initial_state = {
        "steps": graph_steps,
        "current_index": 0,
        "accumulated_outputs": [],
        "current_step_input": None,
        "done": False,
        "auth_header": auth_header,
        "previous_output": "",
        "user_input": body.user_input,
    }

    graph = get_pipeline_graph()
    result = graph.invoke(initial_state)

    step_results = result["accumulated_outputs"]
    final_status = "completed"
    for sr in step_results:
        s_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        matching_step = next((s for s in steps if s["step_order"] == sr["step_order"]), None)
        step_runs_repo.create(
            {
                "run_id": run_id,
                "step_order": sr["step_order"],
                "agent_role_id": matching_step["agent_role_id"] if matching_step else 0,
                "agent_role_name": sr["agent_name"],
                "input_data": json.dumps(sr.get("messages", []), ensure_ascii=False),
                "output_data": sr["output"],
                "ai_response_raw": sr["output"] if sr["status"] == "completed" else "",
                "tokens_used": sr.get("tokens", 0),
                "status": sr["status"],
                "started_at": s_now,
                "completed_at": s_now,
            }
        )
        if sr["status"] == "failed":
            final_status = "failed"

    c_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    runs_repo.update(
        run_id,
        {
            "status": final_status,
            "result": json.dumps({"steps": step_results}, ensure_ascii=False),
            "completed_at": c_now,
        },
    )
    return success(data={"run_id": run_id, "status": final_status, "steps": step_results})


@router.get("/{pipeline_id}/runs")
def list_runs(
    pipeline_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(require_scope("visit")),
    db=Depends(get_db),
):
    """分页查询指定管道的运行历史。
    Args: pipeline_id (int) 管道ID; page (int) 页码; page_size (int) 每页条数; current_user 用户; db SQLite连接。
    Returns: dict 成功响应"""
    pipelines_repo = AgentPipelinesRepository(db)
    runs_repo = PipelineRunsRepository(db)
    _p404(pipelines_repo, pipeline_id)
    total, total_pages, rows = runs_repo.paginate(
        page=page,
        page_size=page_size,
        conditions=["pipeline_id=?"],
        params=[pipeline_id],
        order_by="started_at DESC",
    )
    return success(
        data=PaginatedResponse(
            items=rows,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )
