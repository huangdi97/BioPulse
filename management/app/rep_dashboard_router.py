"""代表仪表盘路由。聚合拜访、任务、费用预检、推荐等端点。"""

import logging

import httpx
from fastapi import APIRouter, Query

from shared.ai_gateway import INTERNAL_API_TIMEOUT
from shared.app_settings import settings
from shared.base import success

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rep", tags=["代表看板"])
CLOUD_API = settings.cloud_api_base
ASSISTANT_API = settings.assistant_api_base


async def _fetch(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, timeout=INTERNAL_API_TIMEOUT)
            return resp.json() if resp.status_code == 200 else {}
        except Exception:
            logger.warning("rep_dashboard fetch failed: %s", url, exc_info=True)
            return {}


@router.get("/dashboard", summary="代表总览")
async def rep_dashboard(user_id: int = Query(..., description="用户 ID")):
    tasks, visits, compliance = await _fetch(f"{ASSISTANT_API}/api/assistant/tasks?user_id={user_id}")
    return success(
        data={
            "user_id": user_id,
            "pending_tasks": tasks,
            "today_visits": visits,
            "compliance_alerts": compliance,
        }
    )


@router.get("/dashboard/today-recommendations", summary="今日推荐")
async def today_recommendations(user_id: int = Query(..., description="用户 ID")):
    r1 = _fetch(f"{CLOUD_API}/api/cloud/recommend/generate?user_id={user_id}")
    r2 = _fetch(f"{ASSISTANT_API}/api/assistant/visit-reason/generate?user_id={user_id}")
    r3 = _fetch(f"{CLOUD_API}/api/cloud/expense/precheck/alerts?user_id={user_id}")
    results = await r1, await r2, await r3
    return success(
        data={
            "recommendations": _extract_list(results[0], "data"),
            "visit_reasons": _extract_list(results[1], "reasons"),
            "expense_alerts": _extract_list(results[2], "alerts"),
        }
    )


@router.get("/dashboard/visit-autofill", summary="拜访自动填表")
async def visit_autofill(text: str = Query(..., description="拜访要点文本")):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{ASSISTANT_API}/api/assistant/visit-autofill/extract",
                json={"text": text},
                timeout=INTERNAL_API_TIMEOUT,
            )
            data = resp.json() if resp.status_code == 200 else {}
        except Exception:
            logger.warning("visit_autofill proxy failed", exc_info=True)
            data = {}
    return success(data=data)


@router.get("/dashboard/expense-precheck/{expense_id}", summary="费用预检")
async def expense_precheck(expense_id: int):
    data = await _fetch(f"{CLOUD_API}/api/cloud/expense/precheck/{expense_id}")
    return success(data=data)


@router.get("/dashboard/visit-reason", summary="拜访理由")
async def visit_reason(
    hcp_name: str = Query(..., description="医生姓名"),
    product: str = Query("", description="推广产品"),
    goal: str = Query("", description="拜访目标"),
):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{ASSISTANT_API}/api/assistant/visit-reason/generate",
                json={"hcp_name": hcp_name, "product": product, "goal": goal},
                timeout=INTERNAL_API_TIMEOUT,
            )
            data = resp.json() if resp.status_code == 200 else {}
        except Exception:
            logger.warning("visit_reason proxy failed", exc_info=True)
            data = {}
    return success(data=data)


def _extract_list(data: dict, key: str) -> list:
    if isinstance(data, dict):
        inner = data.get("data") or data
        if isinstance(inner, dict):
            return inner.get(key, [])
        return []
    return []
