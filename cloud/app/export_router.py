from typing import Any

from fastapi import APIRouter, Depends

from cloud.app.services.export_service import ExportService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/export", tags=["数据导出"])


@router.get("/audit-logs")
def export_audit_logs(
    current_user: dict = Depends(require_scope("visit")),
    service: ExportService = Depends(),
) -> Any:
    return success(data=service.export_audit_logs())


@router.get("/customers")
def export_customers(
    current_user: dict = Depends(require_scope("visit")),
    service: ExportService = Depends(),
) -> Any:
    return success(data=service.export_customers())
