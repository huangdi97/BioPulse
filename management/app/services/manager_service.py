"""经理服务模块。提供团队统计、成员、合规和绩效数据的聚合查询。"""

import httpx

CLOUD_API = "http://localhost:8000"


async def _fetch(path: str) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{CLOUD_API}{path}", timeout=10)
            return resp.json() if resp.status_code == 200 else {}
        except Exception:
            return {}


async def get_team_stats(team_id: int) -> dict:
    dashboard = await _fetch("/api/demo/dashboard")
    users = await _fetch("/api/demo/dashboard/users")
    compliance = await _fetch("/api/demo/dashboard/compliance")
    return {
        "team_id": team_id,
        "overview": dashboard,
        "users": users,
        "compliance": compliance,
    }


async def get_team_members(team_id: int) -> dict:
    data = await _fetch("/api/demo/dashboard")
    members = data.get("members", []) if data else []
    return {
        "team_id": team_id,
        "members": members,
        "total": len(members),
    }


async def get_team_compliance(team_id: int) -> dict:
    data = await _fetch("/api/demo/dashboard/compliance")
    if not data:
        return {"team_id": team_id, "compliance": {}}
    return {
        "team_id": team_id,
        "compliance": data,
    }


async def get_team_performance(team_id: int) -> dict:
    dashboard = await _fetch("/api/demo/dashboard")
    perf = dashboard.get("performance", {}) if dashboard else {}
    return {
        "team_id": team_id,
        "performance": perf,
    }
