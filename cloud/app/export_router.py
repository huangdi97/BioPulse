from typing import Any

from fastapi import APIRouter, Depends

from shared.auth import get_current_user
from shared.base import success
from cloud.app.services.export_service import ExportService

router = APIRouter(prefix="/export", tags=["数据导出"])


@router.get("/audit-logs")
def export_audit_logs(
    current_user: dict = Depends(get_current_user),
    service: ExportService = Depends(),
) -> Any:
    return success(data=service.export_audit_logs())


@router.get("/customers")
def export_customers(
    current_user: dict = Depends(get_current_user),
    service: ExportService = Depends(),
) -> Any:
    return success(data=service.export_customers())
