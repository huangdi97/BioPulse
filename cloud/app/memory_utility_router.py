from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from cloud.app.services.memory_utility_service import MemoryUtilityService
from shared.base import success

router = APIRouter(prefix="/memory-utils", tags=["Memory Utilities"])


class MoveRequest(BaseModel):
    new_parent_id: int


@router.post("/tree/subtree-stats/{node_id}")
def subtree_stats(node_id: int, service: MemoryUtilityService = Depends()):
    return success(data=service.subtree_stats(node_id))


@router.post("/tree/move/{node_id}")
def move_node(node_id: int, body: MoveRequest, service: MemoryUtilityService = Depends()):
    result = service.move_node(node_id, body.new_parent_id)
    return success(message=result.get("message"))


@router.get("/tree/heatmap")
def tree_heatmap(service: MemoryUtilityService = Depends()):
    return success(data=service.tree_heatmap())


@router.get("/tree/duplicates/{node_id}")
def tree_duplicates(node_id: int, service: MemoryUtilityService = Depends()):
    return success(data=service.tree_duplicates(node_id))


@router.delete("/tree/prune/{node_id}")
def prune_node(node_id: int, service: MemoryUtilityService = Depends()):
    result = service.prune_node(node_id)
    return success(data={"deleted_count": result["deleted_count"]}, message=result.get("message"))


@router.post("/utility/score/{memory_id}")
def score_memory(memory_id: int, service: MemoryUtilityService = Depends()):
    return success(data=service.score_memory(memory_id))


@router.post("/utility/score-all")
def score_all(service: MemoryUtilityService = Depends()):
    return success(data=service.score_all())


@router.get("/utility/rankings")
def utility_rankings(
    min_utility: float = Query(0.0),
    limit: int = Query(20, ge=1, le=200),
    service: MemoryUtilityService = Depends(),
):
    return success(data=service.utility_rankings(min_utility=min_utility, limit=limit))


@router.post("/sleep/consolidate")
def sleep_consolidate(service: MemoryUtilityService = Depends()):
    return success(data=service.sleep_consolidate())


@router.get("/sleep/history")
def sleep_history(service: MemoryUtilityService = Depends()):
    return success(data=service.sleep_history())
