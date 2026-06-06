"""总裁服务模块。提供全局概览、合规总览、团队排名和趋势报告。"""

import httpx

CLOUD_API = "http://localhost:8000"


async def _fetch(path: str) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{CLOUD_API}{path}", timeout=10)
            return resp.json() if resp.status_code == 200 else {}
        except Exception:
            return {}


async def get_summary() -> dict:
    dashboard = await _fetch("/api/demo/dashboard")
    users = await _fetch("/api/demo/dashboard/users")
    compliance = await _fetch("/api/demo/dashboard/compliance")
    return {
        "dashboard": dashboard,
        "users": users,
        "compliance": compliance,
    }


async def get_compliance_overview() -> dict:
    data = await _fetch("/api/demo/dashboard/compliance")
    if not data:
        return {"compliance_overview": {}}
    return {"compliance_overview": data}


async def get_team_rankings() -> dict:
    dashboard = await _fetch("/api/demo/dashboard")
    users = await _fetch("/api/demo/dashboard/users")
    teams = dashboard.get("teams", []) if dashboard else []
    return {
        "rankings": sorted(teams, key=lambda t: t.get("score", 0), reverse=True),
        "user_stats": users,
    }


async def get_trend_report() -> dict:
    dashboard = await _fetch("/api/demo/dashboard")
    compliance = await _fetch("/api/demo/dashboard/compliance")
    return {
        "trend": dashboard.get("trend", {}) if dashboard else {},
        "compliance_trend": compliance.get("trend", {}) if compliance else {},
    }
