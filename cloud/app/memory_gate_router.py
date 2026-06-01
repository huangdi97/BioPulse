from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from cloud.app.services.memory_gate_service import MemoryGateService
from shared.auth_scope import require_scope
from shared.base import PaginatedResponse, success

router = APIRouter(prefix="/memory", tags=["记忆系统"])


class GateCreate(BaseModel):
    name: str
    source_type: str
    importance_threshold: float = 0.5
    ttl_days: int = 90
    retention_policy: str = "normal"


class EntryCreate(BaseModel):
    title: str
    content: str
    memory_type: str = "insight"
    source_type: str = ""
    source_id: Optional[str] = None
    importance: float = 0.5
    context_tags: list[str] = []


class RecallRequest(BaseModel):
    query: str
    memory_types: list[str] = []
    min_importance: float = 0.5
    max_results: int = 10


@router.post("/gates", status_code=201)
def create_gate(
    body: GateCreate,
    request: Request,
    current_user=Depends(require_scope("visit")),
    service: MemoryGateService = Depends(),
):
    result = service.create_gate(
        name=body.name,
        source_type=body.source_type,
        importance_threshold=body.importance_threshold,
        ttl_days=body.ttl_days,
        retention_policy=body.retention_policy,
    )
    return success(data=result)


@router.get("/gates")
def list_gates(service: MemoryGateService = Depends()):
    return success(data=service.list_gates())


@router.post("/entries", status_code=201)
def create_entry(
    body: EntryCreate,
    request: Request,
    current_user=Depends(require_scope("visit")),
    service: MemoryGateService = Depends(),
):
    uid = int(current_user["sub"])
    result = service.create_entry(
        title=body.title,
        content=body.content,
        memory_type=body.memory_type,
        source_type=body.source_type,
        source_id=body.source_id,
        importance=body.importance,
        context_tags=body.context_tags,
        uid=uid,
    )
    return success(data=result)


@router.get("/entries")
def list_entries(
    memory_type: Optional[str] = Query(None),
    importance_min: Optional[float] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: MemoryGateService = Depends(),
):
    total, total_pages, items = service.list_entries(
        memory_type=memory_type,
        importance_min=importance_min,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/entries/{entry_id}")
def get_entry(entry_id: int, service: MemoryGateService = Depends()):
    return success(data=service.get_entry(entry_id))


@router.post("/recall")
def recall(
    body: RecallRequest,
    request: Request,
    current_user=Depends(require_scope("visit")),
    service: MemoryGateService = Depends(),
):
    result = service.recall(
        query=body.query,
        memory_types=body.memory_types,
        min_importance=body.min_importance,
        max_results=body.max_results,
    )
    return success(data=result)


@router.post("/auto-store/{source_type}/{source_id}")
def auto_store(
    source_type: str,
    source_id: str,
    request: Request,
    current_user=Depends(require_scope("visit")),
    service: MemoryGateService = Depends(),
):
    uid = int(current_user["sub"])
    auth = request.headers.get("Authorization", "")
    return success(
        data=service.auto_store(
            source_type=source_type,
            source_id=source_id,
            uid=uid,
            auth_header=auth,
        )
    )


@router.get("/dashboard")
def dashboard(service: MemoryGateService = Depends()):
    return success(data=service.dashboard())
