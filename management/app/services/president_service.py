"""总裁服务模块。提供全局概览、合规总览、团队排名和趋势报告。"""

import logging

import httpx

from management.app.services._shared import fetch
from shared.app_settings import settings

logger = logging.getLogger(__name__)

CLOUD_API = settings.cloud_api_base


async def get_summary() -> dict:
    """获取全局概览，包含仪表盘、用户和合规数据。

    Returns:
        dict: 包含 dashboard、users、compliance 的全局概览字典。
    """
    dashboard = await fetch("/api/demo/dashboard")
    users = await fetch("/api/demo/dashboard/users")
    compliance = await fetch("/api/demo/dashboard/compliance")
    return {
        "dashboard": dashboard,
        "users": users,
        "compliance": compliance,
    }


async def get_compliance_overview() -> dict:
    """获取全局合规总览。

    Returns:
        dict: 包含 compliance_overview 合规总览数据的字典。
    """
    data = await fetch("/api/demo/dashboard/compliance")
    if not data:
        return {"compliance_overview": {}}
    return {"compliance_overview": data}


async def get_team_rankings() -> dict:
    """获取团队排名，按评分降序排列。

    Returns:
        dict: 包含 rankings 排名列表和 user_stats 用户统计的字典。
    """
    dashboard = await fetch("/api/demo/dashboard")
    users = await fetch("/api/demo/dashboard/users")
    teams = dashboard.get("teams", []) if dashboard else []
    return {
        "rankings": sorted(teams, key=lambda t: t.get("score", 0), reverse=True),
        "user_stats": users,
    }


async def get_trend_report() -> dict:
    """获取趋势报告，包含仪表盘趋势和合规趋势。

    Returns:
        dict: 包含 trend 和 compliance_trend 趋势数据的字典。
    """
    dashboard = await fetch("/api/demo/dashboard")
    compliance = await fetch("/api/demo/dashboard/compliance")
    return {
        "trend": dashboard.get("trend", {}) if dashboard else {},
        "compliance_trend": compliance.get("trend", {}) if compliance else {},
    }
