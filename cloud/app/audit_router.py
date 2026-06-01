from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from shared.auth_scope import require_scope
from shared.base import success
from cloud.app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["审计日志"])


class AuditLogCreate(BaseModel):
    user_id: int
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    detail: str = ""
    source_end: str = "cloud"
    ip_address: str = ""


@router.post("/logs")
def create_audit_log(
    body: AuditLogCreate,
    current_user: dict = Depends(require_scope("visit")),
    service: AuditService = Depends(),
) -> Any:
    service.create_log(
        user_id=body.user_id,
        action=body.action,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        detail=body.detail,
        source_end=body.source_end,
        ip_address=body.ip_address,
    )
    return success(message="audit log recorded")


@router.get("/logs")
def list_audit_logs(
    entity_type: str = Query(None),
    entity_id: int = Query(None),
    action: str = Query(None),
    user_id: int = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_scope("visit")),
    service: AuditService = Depends(),
) -> Any:
    result = service.list_logs(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        user_id=user_id,
        page=page,
        page_size=page_size,
    )
    return success(data=result)


@router.get("/logs/stats")
def audit_stats(
    current_user: dict = Depends(require_scope("visit")),
    service: AuditService = Depends(),
) -> Any:
    return success(data=service.get_stats())
