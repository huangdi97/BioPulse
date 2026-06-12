"""仪表盘路由。聚合展示全局仪表盘、用户统计和合规数据。"""

import logging

import httpx
from fastapi import APIRouter

from shared.ai_gateway import INTERNAL_API_TIMEOUT
from shared.app_settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dashboard"])
CLOUD_API = settings.cloud_api_base


async def _fetch(path: str) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{CLOUD_API}{path}", timeout=INTERNAL_API_TIMEOUT)
            return resp.json() if resp.status_code == 200 else {}
        except Exception:
            logger.warning("Dashboard router数据获取异常", exc_info=True)
            return {"_degraded": True, "_from_cache": True}


@router.get("/api/management/dashboard", tags=["看板"])
async def dashboard():
    data = await _fetch("/api/demo/dashboard")
    return {"code": 0, "message": "ok", "data": data}


@router.get("/api/management/dashboard/users", tags=["看板"])
async def dashboard_users():
    data = await _fetch("/api/demo/dashboard/users")
    return {"code": 0, "message": "ok", "data": data}


@router.get("/api/management/dashboard/compliance", tags=["看板"])
async def dashboard_compliance():
    data = await _fetch("/api/demo/dashboard/compliance")
    return {"code": 0, "message": "ok", "data": data}


@router.get("/api/management/dashboard/overview", tags=["看板"])
async def dashboard_overview():
    async with httpx.AsyncClient() as client:
        try:
            r1 = await client.get(f"{CLOUD_API}/api/demo/dashboard", timeout=INTERNAL_API_TIMEOUT)
            r2 = await client.get(f"{CLOUD_API}/api/demo/dashboard/users", timeout=INTERNAL_API_TIMEOUT)
            r3 = await client.get(f"{CLOUD_API}/api/demo/dashboard/compliance", timeout=INTERNAL_API_TIMEOUT)
            aggregated = {
                "overview": r1.json() if r1.status_code == 200 else {},
                "users": r2.json() if r2.status_code == 200 else {},
                "compliance": r3.json() if r3.status_code == 200 else {},
            }
        except Exception:
            logger.warning("Dashboard router聚合异常", exc_info=True)
            aggregated = {"_degraded": True, "_from_cache": True}
    return {"code": 0, "message": "ok", "data": aggregated}
