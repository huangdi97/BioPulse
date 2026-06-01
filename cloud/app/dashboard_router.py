from typing import Any

from fastapi import APIRouter, Depends

from shared.auth import get_current_user
from shared.base import success
from cloud.app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
def overview(
    current_user: dict = Depends(get_current_user),
    service: DashboardService = Depends(),
) -> Any:
    return success(data=service.get_overview())


@router.get("/users")
def user_stats(
    current_user: dict = Depends(get_current_user),
    service: DashboardService = Depends(),
) -> Any:
    return success(data=service.get_user_stats())


@router.get("/compliance")
def compliance_stats(
    current_user: dict = Depends(get_current_user),
    service: DashboardService = Depends(),
) -> Any:
    return success(data=service.get_compliance_stats())


@router.get("/contents")
def content_stats(
    current_user: dict = Depends(get_current_user),
    service: DashboardService = Depends(),
) -> Any:
    return success(data=service.get_content_stats())
