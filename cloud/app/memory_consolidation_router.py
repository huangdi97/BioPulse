from fastapi import APIRouter, Depends
from pydantic import BaseModel

from cloud.app.services.memory_consolidation_service import MemoryConsolidationService
from shared.auth import get_current_user
from shared.base import success

router = APIRouter(prefix="/memory/consolidation", tags=["记忆系统"])


class MemoryEvaluateRequest(BaseModel):
    agent_id: str


@router.post("/trigger")
def trigger_consolidation(
    current_user=Depends(get_current_user),
    service: MemoryConsolidationService = Depends(),
):
    result = service.trigger_consolidation(
        triggered_by=current_user.get("sub", ""),
    )
    return success(data=result)


@router.get("/status")
def consolidation_status(
    current_user=Depends(get_current_user),
    service: MemoryConsolidationService = Depends(),
):
    return success(data=service.consolidation_status())


@router.post("/evaluate")
def evaluate_memory(
    body: MemoryEvaluateRequest,
    current_user=Depends(get_current_user),
    service: MemoryConsolidationService = Depends(),
):
    return success(data=service.evaluate_memory(agent_id=body.agent_id))


@router.get("/evaluate/trend")
def evaluate_trend(
    current_user=Depends(get_current_user),
    service: MemoryConsolidationService = Depends(),
):
    return success(data=service.evaluate_trend())
