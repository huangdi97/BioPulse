"""患者招募服务。"""

from datetime import datetime, timezone

import httpx

from ..database import get_cache, set_cache

CLOUD_API = "http://localhost:8000"


async def get_recruitment_status(trial_id: str) -> dict:
    """查询临床试验的招募进度。

    调用 Cloud 服务获取患者招募数据，
    返回招募状态、已入组数、目标数和时间线。
    """
    cache_key = f"recruitment:status:{trial_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{CLOUD_API}/kg/entities",
            params={
                "name": trial_id,
                "entity_type": "trial",
            },
        )
        entities = []
        if resp.status_code == 200:
            data = resp.json()
            entities = data.get("data", data.get("entities", []))

    result = _build_recruitment_status(trial_id, entities)
    set_cache(cache_key, result, ttl=600)
    return result


def _build_recruitment_status(trial_id: str, entities: list) -> dict:
    """构建招募进度数据。"""
    entity = entities[0] if entities else {}
    props = entity.get("properties", {})

    enrolled = props.get("enrolled", 0)
    target = props.get("target", 100)
    completion_pct = round((enrolled / target) * 100, 1) if target > 0 else 0

    return {
        "trial_id": trial_id,
        "trial_name": props.get("name", f"试验 {trial_id}"),
        "indication": props.get("indication", ""),
        "status": props.get("recruitment_status", "recruiting"),
        "enrolled": enrolled,
        "target": target,
        "completion_pct": completion_pct,
        "screening_failures": props.get("screening_failures", 0),
        "dropouts": props.get("dropouts", 0),
        "sites": props.get("sites", 3),
        "timeline": {
            "start_date": props.get("start_date", ""),
            "estimated_end": props.get("estimated_end", ""),
            "actual_end": props.get("actual_end", None),
        },
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


async def get_pipeline() -> dict:
    """获取患者招募管线总览。

    汇总所有在研试验的招募进度，
    返回管线概览、阶段分布和关键指标。
    """
    cache_key = "recruitment:pipeline"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{CLOUD_API}/kg/entities/list",
            params={
                "entity_type": "trial",
                "status": "active",
            },
        )
        entities = []
        if resp.status_code == 200:
            data = resp.json()
            entities = data.get("data", data.get("entities", []))

    result = _build_pipeline(entities)
    set_cache(cache_key, result, ttl=600)
    return result


def _build_pipeline(entities: list) -> dict:
    """构建管线总览数据。"""
    trials = []
    total_enrolled = 0
    total_target = 0
    phase_distribution = {}

    for entity in entities[:20]:
        props = entity.get("properties", {})
        phase = props.get("phase", "I期")
        enrolled = props.get("enrolled", 0)
        target = props.get("target", 100)

        total_enrolled += enrolled
        total_target += target
        phase_distribution[phase] = phase_distribution.get(phase, 0) + 1

        trials.append(
            {
                "trial_id": entity.get("entity_id", ""),
                "trial_name": props.get("name", ""),
                "indication": props.get("indication", ""),
                "phase": phase,
                "status": props.get("recruitment_status", "recruiting"),
                "enrolled": enrolled,
                "target": target,
                "completion_pct": round((enrolled / target) * 100, 1) if target > 0 else 0,
            }
        )

    return {
        "total_trials": len(trials),
        "total_enrolled": total_enrolled,
        "total_target": total_target,
        "overall_completion_pct": round((total_enrolled / total_target) * 100, 1) if total_target > 0 else 0,
        "phase_distribution": phase_distribution,
        "trials": trials,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
