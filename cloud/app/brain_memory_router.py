from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from cloud.app.services.brain_memory_service import BrainMemoryService
from shared.auth_scope import require_scope
from shared.base import success, PaginatedResponse

router = APIRouter(prefix="/brain-memory", tags=["Brain Memory"])


class WorkingMemorySet(BaseModel):
    session_id: str
    slot_key: str
    slot_value: str = ""
    slot_type: str = "string"
    ttl_seconds: int = 1800


class EpisodicStore(BaseModel):
    event_type: str
    title: str
    description: str = ""
    context: dict = {}
    outcome: str = ""
    valence: float = 0.0
    intensity: float = 0.5
    involved_agents: list[str] = []
    related_entity_type: str = ""
    related_entity_id: Optional[int] = None


class SemanticAbstract(BaseModel):
    source_type: str
    source_id: str
    abstraction_level: str = "medium"


class ProceduralLearn(BaseModel):
    pattern_name: str
    trigger_conditions: str = ""
    action_sequence: str = ""
    success_rate: float = 0.5


class ProceduralRecall(BaseModel):
    trigger_context: str = ""


class MemoryDecay(BaseModel):
    hours_threshold: int = 72


@router.post("/working/set")
def working_set(body: WorkingMemorySet, service: BrainMemoryService = Depends()):
    result = service.working_set(
        session_id=body.session_id,
        slot_key=body.slot_key,
        slot_value=body.slot_value,
        slot_type=body.slot_type,
        ttl_seconds=body.ttl_seconds,
    )
    return success(data=result)


@router.get("/working/get")
def working_get(
    session_id: str = Query(...),
    slot_key: Optional[str] = Query(None),
    service: BrainMemoryService = Depends(),
):
    result = service.working_get(session_id=session_id, slot_key=slot_key)
    return success(data=result["data"])


@router.delete("/working/clear/{session_id}")
def working_clear(session_id: str, service: BrainMemoryService = Depends()):
    message = service.working_clear(session_id)
    return success(message=message)


@router.post("/working/refresh/{session_id}")
def working_refresh(session_id: str, service: BrainMemoryService = Depends()):
    result = service.working_refresh(session_id)
    return success(data=result)


@router.post("/episodic/store", status_code=201)
def episodic_store(
    body: EpisodicStore,
    request: Request,
    current_user=Depends(require_scope("visit")),
    service: BrainMemoryService = Depends(),
):
    uid = str(current_user["sub"])
    result = service.episodic_store(
        event_type=body.event_type,
        title=body.title,
        description=body.description,
        context=body.context,
        outcome=body.outcome,
        valence=body.valence,
        intensity=body.intensity,
        involved_agents=body.involved_agents,
        related_entity_type=body.related_entity_type,
        related_entity_id=body.related_entity_id,
        uid=uid,
    )
    return success(data=result)


@router.get("/episodic/list")
def episodic_list(
    event_type: Optional[str] = Query(None),
    outcome: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: BrainMemoryService = Depends(),
):
    result = service.episodic_list(
        event_type=event_type,
        outcome=outcome,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return success(
        data=PaginatedResponse(
            items=result["items"],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )
    )


@router.get("/episodic/{memory_id}")
def episodic_detail(memory_id: int, service: BrainMemoryService = Depends()):
    row = service.episodic_detail(memory_id)
    return success(data=row)


@router.post("/episodic/{memory_id}/consolidate")
def episodic_consolidate(
    memory_id: int,
    request: Request,
    service: BrainMemoryService = Depends(),
):
    auth_header = request.headers.get("Authorization", "")
    result = service.episodic_consolidate(memory_id, auth_header)
    return success(data=result)


@router.get("/dashboard")
def dashboard(service: BrainMemoryService = Depends()):
    result = service.dashboard()
    return success(data=result)


@router.post("/semantic/abstract")
def semantic_abstract(
    body: SemanticAbstract, request: Request, service: BrainMemoryService = Depends()
):
    result = service.semantic_abstract(
        source_type=body.source_type,
        source_id=body.source_id,
        abstraction_level=body.abstraction_level,
        auth_header=request.headers.get("Authorization", ""),
    )
    return success(data=result)


@router.get("/semantic/search")
def semantic_search(
    query: str = Query(...),
    limit: int = Query(10, ge=1, le=100),
    service: BrainMemoryService = Depends(),
):
    result = service.semantic_search(query=query, limit=limit)
    return success(data=result)


@router.post("/procedural/learn")
def procedural_learn(body: ProceduralLearn, service: BrainMemoryService = Depends()):
    result = service.procedural_learn(
        pattern_name=body.pattern_name,
        trigger_conditions=body.trigger_conditions,
        action_sequence=body.action_sequence,
        success_rate=body.success_rate,
    )
    return success(data=result)


@router.post("/procedural/recall")
def procedural_recall(body: ProceduralRecall, service: BrainMemoryService = Depends()):
    result = service.procedural_recall(trigger_context=body.trigger_context)
    return success(data=result)


@router.post("/decay")
def memory_decay(body: MemoryDecay, service: BrainMemoryService = Depends()):
    result = service.memory_decay(hours_threshold=body.hours_threshold)
    return success(data=result)
