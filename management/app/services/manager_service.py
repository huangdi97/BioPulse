"""经理服务模块。提供团队统计、成员、合规和绩效数据的聚合查询。"""

import logging

import httpx

from management.app.services._shared import fetch
from shared.app_settings import settings

logger = logging.getLogger(__name__)

CLOUD_API = settings.cloud_api_base


async def get_team_stats(team_id: int) -> dict:
    """获取团队统计总览，包含仪表盘、用户列表和合规数据。

    Args:
        team_id: 团队 ID。

    Returns:
        dict: 包含 team_id、overview、users、compliance 的字典。
    """
    dashboard = await fetch("/api/demo/dashboard")
    users = await fetch("/api/demo/dashboard/users")
    compliance = await fetch("/api/demo/dashboard/compliance")
    return {
        "team_id": team_id,
        "overview": dashboard,
        "users": users,
        "compliance": compliance,
    }


async def get_team_members(team_id: int) -> dict:
    """获取团队成员列表及总人数。

    Args:
        team_id: 团队 ID。

    Returns:
        dict: 包含 team_id、members 列表和 total 计数的字典。
    """
    data = await fetch("/api/demo/dashboard")
    members = data.get("members", []) if data else []
    return {
        "team_id": team_id,
        "members": members,
        "total": len(members),
    }


async def get_team_compliance(team_id: int) -> dict:
    """获取团队合规数据。

    Args:
        team_id: 团队 ID。

    Returns:
        dict: 包含 team_id 和 compliance 合规信息的字典。
    """
    data = await fetch("/api/demo/dashboard/compliance")
    if not data:
        return {"team_id": team_id, "compliance": {}}
    return {
        "team_id": team_id,
        "compliance": data,
    }


async def get_team_performance(team_id: int) -> dict:
    """获取团队绩效数据。

    Args:
        team_id: 团队 ID。

    Returns:
        dict: 包含 team_id 和 performance 绩效信息的字典。
    """
    dashboard = await fetch("/api/demo/dashboard")
    perf = dashboard.get("performance", {}) if dashboard else {}
    return {
        "team_id": team_id,
        "performance": perf,
    }
