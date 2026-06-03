from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from cloud.app.services.brain_evolution_service import BrainEvolutionService
from cloud.app.services.brain_orchestrator_service import BrainOrchestratorService
from cloud.app.services.brain_search_service import BrainSearchService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/memory/brain", tags=["类脑记忆"])


class SensoryIngest(BaseModel):
    """SensoryIngest 服务类。"""

    input_type: str = "message"
    raw_content: str = ""
    source: str = ""


class CreateProcedural(BaseModel):
    """CreateProcedural 服务类。"""

    procedure_key: str
    name: str = ""
    description: str = ""
    steps: str = "[]"
    trigger_conditions: str = "[]"


class InvokeProcedural(BaseModel):
    """InvokeProcedural 服务类。"""

    context: dict = {}


class Orchestrate(BaseModel):
    """Orchestrate 服务类。"""

    input_text: str = ""
    input_type: str = "message"
    source: str = ""


class EvolveMemory(BaseModel):
    """EvolveMemory 服务类。"""

    memory_id: int
    new_evidence: str = ""
    memory_type: str = "episodic"


class FoldMemories(BaseModel):
    """FoldMemories 服务类。"""

    memory_ids: list[int]


@router.post("/sensory/ingest", summary="Sensory Ingest")
def sensory_ingest(
    body: SensoryIngest,
    service: BrainOrchestratorService = Depends(),
    _user=Depends(require_scope("pharma")),
):
    """sensory_ingest 操作。

    Args:
        service: 描述
        _user: 描述
    """
    result = service.ingest_sensory(
        input_type=body.input_type,
        raw_content=body.raw_content,
        source=body.source,
    )
    return success(data=result)


@router.get("/sensory/buffer", summary="Sensory Buffer")
def sensory_buffer(
    limit: int = Query(50, ge=1, le=200),
    service: BrainOrchestratorService = Depends(),
    _user=Depends(require_scope("pharma")),
):
    """sensory_buffer 操作。

    Args:
        limit: 描述
        service: 描述
        _user: 描述
    """
    result = service.get_sensory_buffer(limit=limit)
    return success(data=result)


@router.get("/procedural", summary="Procedural List")
def procedural_list(
    trigger_event: Optional[str] = Query(None),
    service: BrainOrchestratorService = Depends(),
    _user=Depends(require_scope("pharma")),
):
    """procedural_list 操作。

    Args:
        trigger_event: 描述
        service: 描述
        _user: 描述
    """
    result = service.list_procedural(trigger_event=trigger_event)
    return success(data=result)


@router.post("/procedural", status_code=201, summary="Procedural Create")
def procedural_create(
    body: CreateProcedural,
    service: BrainOrchestratorService = Depends(),
    _user=Depends(require_scope("pharma")),
):
    """procedural_create 操作。

    Args:
        service: 描述
        _user: 描述
    """
    result = service.create_procedural(
        procedure_key=body.procedure_key,
        name=body.name,
        description=body.description,
        steps=body.steps,
        trigger_conditions=body.trigger_conditions,
    )
    return success(data=result)


@router.post("/procedural/{procedure_key}/invoke", summary="Procedural Invoke")
def procedural_invoke(
    procedure_key: str,
    body: InvokeProcedural,
    service: BrainOrchestratorService = Depends(),
    _user=Depends(require_scope("pharma")),
):
    """procedural_invoke 操作。

    Args:
        procedure_key: 描述
        service: 描述
        _user: 描述
    """
    result = service.invoke_procedural(procedure_key=procedure_key, context=body.context)
    return success(data=result)


@router.post("/orchestrate", summary="Orchestrate")
def orchestrate(
    body: Orchestrate,
    service: BrainOrchestratorService = Depends(),
    _user=Depends(require_scope("pharma")),
):
    """orchestrate 操作。

    Args:
        service: 描述
        _user: 描述
    """
    result = service.orchestrate(
        input_text=body.input_text,
        input_type=body.input_type,
        source=body.source,
    )
    return success(data=result)


@router.post("/evolve", summary="Evolve Memory")
def evolve_memory(
    body: EvolveMemory,
    service: BrainEvolutionService = Depends(),
    _user=Depends(require_scope("pharma")),
):
    """evolve_memory 操作。

    Args:
        service: 描述
        _user: 描述
    """
    result = service.evolve_memory(
        memory_id=body.memory_id,
        new_evidence=body.new_evidence,
        memory_type=body.memory_type,
    )
    return success(data=result)


@router.get("/evolve/history/{memory_id}", summary="Evolution History")
def evolution_history(
    memory_id: int,
    service: BrainEvolutionService = Depends(),
    _user=Depends(require_scope("pharma")),
):
    """evolution_history 操作。

    Args:
        memory_id: 描述
        service: 描述
        _user: 描述
    """
    result = service.get_evolution_history(memory_id=memory_id)
    return success(data=result)


@router.post("/fold", summary="Fold Memories")
def fold_memories(
    body: FoldMemories,
    service: BrainEvolutionService = Depends(),
    _user=Depends(require_scope("pharma")),
):
    """fold_memories 操作。

    Args:
        service: 描述
        _user: 描述
    """
    result = service.fold_memories(memory_ids=body.memory_ids)
    return success(data=result)


@router.get("/search", summary="Unified Search")
def unified_search(
    q: str = Query(..., min_length=1),
    types: Optional[str] = Query(None, description="Comma-separated memory types"),
    limit: int = Query(20, ge=1, le=200),
    service: BrainSearchService = Depends(),
    _user=Depends(require_scope("pharma")),
):
    """unified_search 操作。

    Args:
        q: 描述
        types: 描述
        limit: 描述
        service: 描述
        _user: 描述
    """
    memory_types = types.split(",") if types else None
    result = service.unified_search(query=q, memory_types=memory_types, limit=limit)
    return success(data=result)


@router.get("/fold/{memory_id}", summary="Get Folded by ID")
def get_folded(
    memory_id: int,
    service: BrainEvolutionService = Depends(),
    _user=Depends(require_scope("pharma")),
):
    """get_folded 操作。

    Args:
        memory_id: 描述
        service: 描述
        _user: 描述
    """
    result = service.get_folded(memory_id=memory_id)
    return success(data=result)
