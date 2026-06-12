"""员工服务模块。提供员工个人资料、任务、合规、绩效和趋势数据查询。"""

import logging

import httpx

from shared.ai_gateway import INTERNAL_API_TIMEOUT
from shared.app_settings import settings

logger = logging.getLogger(__name__)

CLOUD_API = settings.cloud_api_base


async def _fetch_dashboard() -> dict:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{CLOUD_API}/api/demo/dashboard", timeout=INTERNAL_API_TIMEOUT)
            return resp.json() if resp.status_code == 200 else {}
        except Exception:
            logger.warning("Employee service数据获取异常", exc_info=True)
            return {}


async def get_my_profile(user_id: int) -> dict:
    """获取当前员工的个人资料。

    Args:
        user_id: 员工用户 ID。

    Returns:
        dict: 包含 user_id 和 profile 个人资料的字典。
    """
    data = await _fetch_dashboard()
    if not data:
        return {}
    return {
        "user_id": user_id,
        "profile": data.get("profile", {}),
    }


async def get_my_tasks(user_id: int) -> dict:
    """获取当前员工的任务列表及总数。

    Args:
        user_id: 员工用户 ID。

    Returns:
        dict: 包含 user_id、tasks 任务列表和 total 计数的字典。
    """
    data = await _fetch_dashboard()
    if not data:
        return {}
    tasks = data.get("tasks", [])
    return {
        "user_id": user_id,
        "tasks": tasks,
        "total": len(tasks),
    }


async def get_my_compliance(user_id: int) -> dict:
    """获取当前员工的合规数据。

    Args:
        user_id: 员工用户 ID。

    Returns:
        dict: 包含 user_id 和 compliance 合规信息的字典。
    """
    data = await _fetch_dashboard()
    if not data:
        return {}
    return {
        "user_id": user_id,
        "compliance": data.get("compliance", {}),
    }


async def get_my_performance(user_id: int) -> dict:
    """获取当前员工的绩效数据。

    Args:
        user_id: 员工用户 ID。

    Returns:
        dict: 包含 user_id 和 performance 绩效信息的字典。
    """
    data = await _fetch_dashboard()
    if not data:
        return {}
    return {
        "user_id": user_id,
        "performance": data.get("performance", {}),
    }


async def get_my_trend(user_id: int) -> dict:
    """获取当前员工的趋势数据。

    Args:
        user_id: 员工用户 ID。

    Returns:
        dict: 包含 user_id 和 trend 趋势信息的字典。
    """
    data = await _fetch_dashboard()
    if not data:
        return {}
    return {
        "user_id": user_id,
        "trend": data.get("trend", {}),
    }
