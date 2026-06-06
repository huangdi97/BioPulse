"""Agent 流水线编排路由。"""

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from starlette import status

from cloud.app.services.agent_pipeline_service import AgentPipelineService
from shared.auth_scope import require_scope

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


@router.post("", status_code=status.HTTP_201_CREATED)
def create_pipeline(
    body: PipelineCreate,
    current_user=Depends(require_scope("visit")),
    service: AgentPipelineService = Depends(),
):
    """创建包含步骤定义的管道。"""
    uid = int(current_user["sub"])
    return service.create_pipeline(body, uid)


@router.get("")
def list_pipelines(
    current_user=Depends(require_scope("visit")),
    service: AgentPipelineService = Depends(),
):
    """获取所有管道列表（含步骤数）。"""
    return service.list_pipelines()


# IMPORTANT: /runs/{run_id} MUST come before /{pipeline_id} to avoid route conflicts
@router.get("/runs/{run_id}")
def get_run(
    run_id: int,
    current_user=Depends(require_scope("visit")),
    service: AgentPipelineService = Depends(),
):
    """获取指定运行ID的运行详情及步骤运行记录。"""
    return service.get_run(run_id)


@router.get("/{pipeline_id}")
def get_pipeline(
    pipeline_id: int,
    current_user=Depends(require_scope("visit")),
    service: AgentPipelineService = Depends(),
):
    """获取管道详情及其所有步骤。"""
    return service.get_pipeline(pipeline_id)


@router.delete("/{pipeline_id}")
def delete_pipeline(
    pipeline_id: int,
    current_user=Depends(require_scope("visit")),
    service: AgentPipelineService = Depends(),
):
    """删除管道及其关联的步骤和运行记录。"""
    return service.delete_pipeline(pipeline_id)


@router.post("/{pipeline_id}/run")
def run_pipeline(
    pipeline_id: int,
    body: PipelineRunRequest,
    request: Request,
    current_user=Depends(require_scope("visit")),
    service: AgentPipelineService = Depends(),
):
    """执行指定管道，遍历各步骤并记录运行结果。"""
    uid = int(current_user["sub"])
    return service.run_pipeline(pipeline_id, body, request, uid)


@router.get("/{pipeline_id}/runs")
def list_runs(
    pipeline_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(require_scope("visit")),
    service: AgentPipelineService = Depends(),
):
    """分页查询指定管道的运行历史。"""
    return service.list_runs(pipeline_id, page, page_size)
