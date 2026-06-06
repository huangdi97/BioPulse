"""仪表盘概览路由。"""

from typing import Any

from fastapi import APIRouter, Depends

from cloud.app.services.dashboard_service import DashboardService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
def overview(
    current_user: dict = Depends(require_scope("visit")),
    service: DashboardService = Depends(),
) -> Any:
    """获取仪表盘概览数据。

    Args:
        current_user: 当前认证用户。
        service: 仪表盘服务实例。

    Returns:
        包含概览数据的响应。
    """
    return success(data=service.get_overview())


@router.get("/users")
def user_stats(
    current_user: dict = Depends(require_scope("visit")),
    service: DashboardService = Depends(),
) -> Any:
    """获取用户统计数据。

    Args:
        current_user: 当前认证用户。
        service: 仪表盘服务实例。

    Returns:
        包含用户统计数据的响应。
    """
    return success(data=service.get_user_stats())


@router.get("/compliance")
def compliance_stats(
    current_user: dict = Depends(require_scope("visit")),
    service: DashboardService = Depends(),
) -> Any:
    """获取合规统计数据。

    Args:
        current_user: 当前认证用户。
        service: 仪表盘服务实例。

    Returns:
        包含合规统计数据的响应。
    """
    return success(data=service.get_compliance_stats())


@router.get("/contents")
def content_stats(
    current_user: dict = Depends(require_scope("visit")),
    service: DashboardService = Depends(),
) -> Any:
    """获取内容统计数据。

    Args:
        current_user: 当前认证用户。
        service: 仪表盘服务实例。

    Returns:
        包含内容统计数据的响应。
    """
    return success(data=service.get_content_stats())
