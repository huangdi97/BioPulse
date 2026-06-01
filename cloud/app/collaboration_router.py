from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from starlette import status

from cloud.app.services.collaboration_service import CollaborationService
from shared.auth import get_current_user
from shared.base import success

router = APIRouter(prefix="/collaboration", tags=["Agent Collaboration"])


class SkillRegister(BaseModel):
    skill_name: str
    agent_role: str
    description: str = ""
    entity_types: list[str] = []
    capabilities: list[str] = []
    confidence: float = 0.5
    priority: int = 100


class SessionCreate(BaseModel):
    task_description: str
    source_entity_id: str = ""
    source_agent_role: str = ""
    orchestrator_agent: str = ""
    routing_strategy: str = "semantic"


class StepAdd(BaseModel):
    agent_role: str
    action_type: str = "process"
    input_summary: str = ""
    entity_id: str = ""


class StepComplete(BaseModel):
    output_summary: str = ""
    status: str = "completed"
    duration_seconds: int = 0


class RouteRequest(BaseModel):
    task_description: str
    entity_type: str = ""
    entity_id: str = ""
    routing_strategy: str = "semantic"


@router.post("/skills/register")
def register_skill(body: SkillRegister,
                   current_user: dict = Depends(get_current_user),
                   service: CollaborationService = Depends()):
    row = service.register_skill(
        skill_name=body.skill_name, agent_role=body.agent_role,
        description=body.description, entity_types=body.entity_types,
        capabilities=body.capabilities, confidence=body.confidence,
        priority=body.priority,
    )
    return success(data=row)


@router.get("/skills/list")
def list_skills(
    agent_role: Optional[str] = Query(None),
    enabled: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
    service: CollaborationService = Depends(),
):
    rows = service.list_skills(agent_role=agent_role, enabled=enabled)
    return success(data=rows)


@router.delete("/skills/{skill_id}")
def delete_skill(skill_id: int,
                 current_user: dict = Depends(get_current_user),
                 service: CollaborationService = Depends()):
    service.delete_skill(skill_id)
    return success(data={"deleted": skill_id})


@router.post("/sessions/create")
def create_session(body: SessionCreate,
                   current_user: dict = Depends(get_current_user),
                   service: CollaborationService = Depends()):
    row = service.create_session(
        task_description=body.task_description,
        source_entity_id=body.source_entity_id,
        source_agent_role=body.source_agent_role,
        orchestrator_agent=body.orchestrator_agent,
        routing_strategy=body.routing_strategy,
    )
    return success(data=row)


@router.post("/sessions/{session_id}/step")
def add_session_step(
    session_id: str, body: StepAdd,
    current_user: dict = Depends(get_current_user),
    service: CollaborationService = Depends(),
):
    row = service.add_session_step(
        session_id=session_id, agent_role=body.agent_role,
        action_type=body.action_type, input_summary=body.input_summary,
        entity_id=body.entity_id,
    )
    return success(data=row)


@router.post("/sessions/{session_id}/step/{step_id}/complete")
def complete_step(
    session_id: str, step_id: int, body: StepComplete,
    current_user: dict = Depends(get_current_user),
    service: CollaborationService = Depends(),
):
    result = service.complete_step(
        session_id=session_id, step_id=step_id,
        output_summary=body.output_summary,
        status_val=body.status,
        duration_seconds=body.duration_seconds,
    )
    return success(data=result)


@router.get("/sessions/list")
def list_sessions(
    status: Optional[str] = Query(None),
    source_agent_role: Optional[str] = Query(None),
    routing_strategy: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    service: CollaborationService = Depends(),
):
    rows = service.list_sessions(
        status=status, source_agent_role=source_agent_role,
        routing_strategy=routing_strategy,
    )
    return success(data=rows)


@router.get("/sessions/{session_id}")
def get_session(session_id: str,
                current_user: dict = Depends(get_current_user),
                service: CollaborationService = Depends()):
    result = service.get_session(session_id)
    return success(data=result)


@router.post("/route")
def semantic_route(body: RouteRequest,
                   current_user: dict = Depends(get_current_user),
                   service: CollaborationService = Depends()):
    result = service.semantic_route(
        task_description=body.task_description,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        routing_strategy=body.routing_strategy,
    )
    return success(data=result)


@router.get("/dashboard")
def dashboard(current_user: dict = Depends(get_current_user),
              service: CollaborationService = Depends()):
    result = service.dashboard()
    return success(data=result)
