"""Sage 记忆引擎路由：评分查询、演化触发、自动链接与状态。"""

from fastapi import APIRouter, Depends

from cloud.app.services.sage_engine_service import SageEngineService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/sage", tags=["记忆系统"], dependencies=[Depends(require_scope("research"))])


@router.get("/score")
def get_all_scores(service: SageEngineService = Depends()):
    return success(data=service.score_all_memories())


@router.get("/score/{memory_type}/{memory_id}")
def get_score_detail(memory_type: str, memory_id: int, service: SageEngineService = Depends()):
    return success(data=service.score_detail(memory_type, memory_id))


@router.post("/evolve")
def evolve(service: SageEngineService = Depends()):
    return success(data=service.evolve(triggered_by="manual"))


@router.post("/auto-link")
def auto_link(service: SageEngineService = Depends()):
    return success(data=service.linking.auto_link())


@router.get("/status")
def get_status(service: SageEngineService = Depends()):
    return success(data=service.linking.get_status())
