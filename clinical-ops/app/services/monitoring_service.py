"""监察报告服务。"""

from datetime import datetime, timezone

import httpx
from clinical_ops.app.database import get_cache, set_cache

CLOUD_API = "http://localhost:8000"


async def get_monitoring_plan(trial_id: str) -> dict:
    """获取临床试验的监察计划。

    查询指定试验的监察计划，包括监察频率、范围和负责人，
    返回完整的监察计划详情。
    """
    cache_key = f"monitoring:plan:{trial_id}"
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

    result = _build_monitoring_plan(trial_id, entities)
    set_cache(cache_key, result, ttl=600)
    return result


def _build_monitoring_plan(trial_id: str, entities: list) -> dict:
    """构建监察计划数据。"""
    entity = entities[0] if entities else {}
    props = entity.get("properties", {})

    return {
        "trial_id": trial_id,
        "trial_name": props.get("name", f"试验 {trial_id}"),
        "monitoring_type": props.get("monitoring_type", "远程监察 + 现场访视"),
        "frequency": props.get("monitoring_frequency", "每月一次"),
        "scope": [
            "知情同意书审核",
            "源数据验证",
            "AE/SAE 报告核查",
            "试验药物管理",
            "CRF 数据完整性",
        ],
        "team": [
            {
                "role": "临床监察员(CRA)",
                "name": props.get("cra_name", "待分配"),
                "email": props.get("cra_email", ""),
            },
            {
                "role": "临床研究协调员(CRC)",
                "name": props.get("crc_name", "待分配"),
                "email": props.get("crc_email", ""),
            },
            {
                "role": "数据管理员",
                "name": props.get("data_manager", "待分配"),
                "email": props.get("dm_email", ""),
            },
        ],
        "risk_based": props.get("risk_based", True),
        "status": props.get("monitoring_status", "active"),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


async def get_monitoring_report(trial_id: str, report_id: str) -> dict:
    """获取指定监察报告。

    查询试验的特定监察报告详情，
    返回报告内容、发现项和建议。
    """
    cache_key = f"monitoring:report:{trial_id}:{report_id}"
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

    result = _build_monitoring_report(trial_id, report_id, entities)
    set_cache(cache_key, result, ttl=600)
    return result


def _build_monitoring_report(trial_id: str, report_id: str, entities: list) -> dict:
    """构建监察报告数据。"""
    entity = entities[0] if entities else {}
    props = entity.get("properties", {})

    findings = [
        {
            "type": "major",
            "description": "2例SAE未在24小时内报告",
            "severity": "高",
            "status": "open",
        },
        {
            "type": "minor",
            "description": "3份知情同意书签名日期缺失",
            "severity": "中",
            "status": "closed",
        },
        {
            "type": "observation",
            "description": "试验药物温度记录有1次超限",
            "severity": "中",
            "status": "in_progress",
        },
    ]

    return {
        "report_id": report_id,
        "trial_id": trial_id,
        "trial_name": props.get("name", f"试验 {trial_id}"),
        "report_type": props.get("report_type", "常规监察"),
        "visit_date": props.get("visit_date", datetime.now(timezone.utc).isoformat()),
        "monitor": props.get("cra_name", "监察员"),
        "sites_visited": props.get("sites_visited", 1),
        "findings": findings,
        "summary": "本次监察发现主要问题2项，次要问题3项，观察项1项。建议加强SAE报告培训。",
        "recommendations": [
            "立即完成SAE补充报告",
            "补签缺失的知情同意书",
            "加强药物温度监控流程",
        ],
        "overall_assessment": "需跟进",
        "status": "draft",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


async def generate_report(trial_id: str) -> dict:
    """生成临床试验监察报告。

    基于试验当前数据自动生成监察报告，
    返回新生成的报告标识和概览。
    """
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

    report_id = f"MR-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    result = _build_generated_report(trial_id, report_id, entities)
    set_cache(f"monitoring:report:{trial_id}:{report_id}", result, ttl=600)
    return result


def _build_generated_report(trial_id: str, report_id: str, entities: list) -> dict:
    """构建新生成的监察报告。"""
    entity = entities[0] if entities else {}
    props = entity.get("properties", {})

    return {
        "report_id": report_id,
        "trial_id": trial_id,
        "trial_name": props.get("name", f"试验 {trial_id}"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_type": "自动生成",
        "sites_monitored": props.get("sites", 1),
        "total_findings": 0,
        "status": "generated",
        "message": f"监察报告 {report_id} 已成功生成",
        "next_steps": [
            "审核报告内容",
            "分配监察员确认",
            "上传相关附件",
        ],
    }
