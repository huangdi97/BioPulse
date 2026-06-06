"""记忆整合路由。"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from cloud.app.services.memory_consolidation_service import MemoryConsolidationService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/memory/consolidation", tags=["记忆系统"])


class MemoryEvaluateRequest(BaseModel):
    agent_id: str


@router.post("/trigger")
def trigger_consolidation(
    current_user=Depends(require_scope("visit")),
    service: MemoryConsolidationService = Depends(),
):
    """触发记忆整合流程。

    Returns:
        整合任务触发结果。
    """
    result = service.trigger_consolidation(
        triggered_by=current_user.get("sub", ""),
    )
    return success(data=result)


@router.get("/status")
def consolidation_status(
    current_user=Depends(require_scope("visit")),
    service: MemoryConsolidationService = Depends(),
):
    """查询记忆整合状态。

    Returns:
        当前整合任务状态信息。
    """
    return success(data=service.consolidation_status())


@router.post("/evaluate")
def evaluate_memory(
    body: MemoryEvaluateRequest,
    current_user=Depends(require_scope("visit")),
    service: MemoryConsolidationService = Depends(),
):
    """评估指定代理的记忆质量。

    Args:
        body: 代理 ID。

    Returns:
        记忆评估结果。
    """
    return success(data=service.evaluate_memory(agent_id=body.agent_id))


@router.get("/evaluate/trend")
def evaluate_trend(
    current_user=Depends(require_scope("visit")),
    service: MemoryConsolidationService = Depends(),
):
    """获取记忆评估趋势数据。

    Returns:
        记忆质量变化趋势。
    """
    return success(data=service.evaluate_trend())
