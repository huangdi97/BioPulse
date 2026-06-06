"""员工服务模块。提供员工个人资料、任务、合规、绩效和趋势数据查询。"""

import httpx

CLOUD_API = "http://localhost:8000"


async def _fetch_dashboard() -> dict:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{CLOUD_API}/api/demo/dashboard", timeout=10)
            return resp.json() if resp.status_code == 200 else {}
        except Exception:
            return {}


async def get_my_profile(user_id: int) -> dict:
    data = await _fetch_dashboard()
    if not data:
        return {}
    return {
        "user_id": user_id,
        "profile": data.get("profile", {}),
    }


async def get_my_tasks(user_id: int) -> dict:
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
    data = await _fetch_dashboard()
    if not data:
        return {}
    return {
        "user_id": user_id,
        "compliance": data.get("compliance", {}),
    }


async def get_my_performance(user_id: int) -> dict:
    data = await _fetch_dashboard()
    if not data:
        return {}
    return {
        "user_id": user_id,
        "performance": data.get("performance", {}),
    }


async def get_my_trend(user_id: int) -> dict:
    data = await _fetch_dashboard()
    if not data:
        return {}
    return {
        "user_id": user_id,
        "trend": data.get("trend", {}),
    }
