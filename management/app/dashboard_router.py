"""仪表盘路由。聚合展示全局仪表盘、用户统计和合规数据。"""

import httpx
from fastapi import APIRouter

router = APIRouter(tags=["dashboard"])
CLOUD_API = "http://localhost:8000"


async def _fetch(path: str) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{CLOUD_API}{path}", timeout=10)
            return resp.json() if resp.status_code == 200 else {}
        except Exception:
            return {"_degraded": True, "_from_cache": True}


@router.get("/api/management/dashboard")
async def dashboard():
    data = await _fetch("/api/demo/dashboard")
    return {"code": 0, "message": "ok", "data": data}


@router.get("/api/management/dashboard/users")
async def dashboard_users():
    data = await _fetch("/api/demo/dashboard/users")
    return {"code": 0, "message": "ok", "data": data}


@router.get("/api/management/dashboard/compliance")
async def dashboard_compliance():
    data = await _fetch("/api/demo/dashboard/compliance")
    return {"code": 0, "message": "ok", "data": data}


@router.get("/api/management/dashboard/overview")
async def dashboard_overview():
    async with httpx.AsyncClient() as client:
        try:
            r1 = await client.get(f"{CLOUD_API}/api/demo/dashboard", timeout=10)
            r2 = await client.get(f"{CLOUD_API}/api/demo/dashboard/users", timeout=10)
            r3 = await client.get(f"{CLOUD_API}/api/demo/dashboard/compliance", timeout=10)
            aggregated = {
                "overview": r1.json() if r1.status_code == 200 else {},
                "users": r2.json() if r2.status_code == 200 else {},
                "compliance": r3.json() if r3.status_code == 200 else {},
            }
        except Exception:
            aggregated = {"_degraded": True, "_from_cache": True}
    return {"code": 0, "message": "ok", "data": aggregated}
