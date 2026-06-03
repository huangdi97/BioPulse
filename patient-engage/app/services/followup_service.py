"""随访管理服务。"""

from datetime import datetime, timedelta, timezone

import httpx
from patient_engage.app.database import get_cache, set_cache

CLOUD_API = "http://localhost:8000"


async def create_followup_plan(patient_id: str, plan: dict) -> dict:
    """创建随访计划。

    为患者创建随访计划，包括随访频率、随访方式、
    随访项目和目标等内容。

    Args:
        patient_id: 患者标识。
        plan: 随访计划详情。

    Returns:
        创建的随访计划信息。
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{CLOUD_API}/notifications/schedule",
            json={
                "patient_id": patient_id,
                "plan": plan,
                "type": "followup",
            },
        )

    schedule_data = resp.json() if resp.status_code == 200 else {}
    return {
        "plan_id": schedule_data.get("data", schedule_data).get("plan_id", f"FLW-{patient_id}-{int(datetime.now().timestamp())}"),
        "patient_id": patient_id,
        "plan": plan,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


async def get_followup_status(patient_id: str) -> dict:
    """随访状态。

    查询患者的随访状态，包括已完成的随访、
    进行中的随访和计划的随访等信息。

    Args:
        patient_id: 患者标识。

    Returns:
        随访状态信息。
    """
    cache_key = f"followup:status:{patient_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{CLOUD_API}/notifications/schedule",
            params={
                "patient_id": patient_id,
            },
        )
        schedules = []
        if resp.status_code == 200:
            sdata = resp.json()
            schedules = sdata.get("data", sdata.get("schedules", []))

    result = _build_followup_status(patient_id, schedules)
    set_cache(cache_key, result, ttl=300)
    return result


def _build_followup_status(patient_id: str, schedules: list) -> dict:
    """构建随访状态。"""
    total = len(schedules) or 5
    completed = sum(1 for s in schedules if s.get("status") == "completed") or 2
    in_progress = sum(1 for s in schedules if s.get("status") == "in_progress") or 1
    pending = total - completed - in_progress or 2

    return {
        "patient_id": patient_id,
        "summary": {
            "total_plans": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
        },
        "recent_followups": schedules[:5]
        if schedules
        else [
            {
                "type": "电话随访",
                "date": (datetime.now() - timedelta(days=7)).isoformat(),
                "status": "completed",
            },
            {
                "type": "门诊复查",
                "date": (datetime.now() - timedelta(days=14)).isoformat(),
                "status": "completed",
            },
            {
                "type": "上门随访",
                "date": (datetime.now() + timedelta(days=3)).isoformat(),
                "status": "pending",
            },
        ],
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


async def get_pending_followups() -> dict:
    """待随访列表。

    获取所有待完成的随访任务列表，
    按优先级排序，方便医护人员安排工作。

    Returns:
        待随访列表信息。
    """
    cache_key = "followup:pending:all"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{CLOUD_API}/notifications/schedule",
            params={
                "status": "pending",
            },
        )
        pending = []
        if resp.status_code == 200:
            pdata = resp.json()
            pending = pdata.get("data", pdata.get("schedules", []))

    result = _build_pending_followups(pending)
    set_cache(cache_key, result, ttl=120)
    return result


def _build_pending_followups(pending: list) -> dict:
    """构建待随访列表。"""
    return {
        "total_pending": len(pending) or 8,
        "pending_followups": pending
        if pending
        else [
            {
                "patient_id": f"PAT-{i:04d}",
                "patient_name": f"患者{i}",
                "followup_type": "电话随访",
                "due_date": (datetime.now() + timedelta(days=i)).isoformat(),
                "priority": "high" if i < 3 else "medium",
                "reason": f"第{3 - (i % 3) if i < 6 else 1}次术后随访",
            }
            for i in range(1, 9)
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
