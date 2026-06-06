"""仪表盘概览路由。"""

from typing import Any

from fastapi import APIRouter, Depends

from cloud.app.services.dashboard_service import DashboardService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", summary="仪表盘概览", description="获取仪表盘概览数据，包含关键指标汇总。")
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


@router.get("/users", summary="用户统计数据", description="获取平台用户统计数据，包括活跃用户、注册数等。")
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


@router.get("/compliance", summary="合规统计数据", description="获取内容合规性统计数据，包括审核通过率等。")
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


@router.get("/contents", summary="内容统计数据", description="获取内容管理统计数据，包括内容总量、分类分布等。")
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


@router.get("/team/summary", summary="团队概览", description="获取团队工作概览汇总数据。")
def team_summary(
    current_user: dict = Depends(require_scope("visit")),
) -> Any:
    return success(data={})


@router.get("/team/ranking", summary="团队排名", description="获取团队成员工作绩效排名数据。")
def team_ranking(
    current_user: dict = Depends(require_scope("visit")),
) -> Any:
    return success(data={})
