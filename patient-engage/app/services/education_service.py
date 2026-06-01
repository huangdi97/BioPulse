"""患者教育服务。"""

import httpx
from datetime import datetime, timezone
from patient_engage.app.database import get_cache, set_cache

CLOUD_API = "http://localhost:8000"


async def get_education_content(disease: str) -> dict:
    """获取疾病教育内容。

    根据疾病名称从 Cloud 知识图谱和论文中检索教育内容，
    包括疾病概述、治疗方案、护理建议等。

    Args:
        disease: 疾病名称。

    Returns:
        包含教育内容的字典。
    """
    cache_key = f"edu:content:{disease}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        kg_resp = await client.get(
            f"{CLOUD_API}/kg/entities",
            params={
                "name": disease,
                "entity_type": "disease",
            },
        )
        kg_data = kg_resp.json() if kg_resp.status_code == 200 else {}

        pub_resp = await client.post(
            f"{CLOUD_API}/pubmed/search",
            json={
                "query": f"{disease} patient education treatment",
                "limit": 10,
            },
        )
        pub_data = pub_resp.json() if pub_resp.status_code == 200 else {}

    result = _build_education_content(disease, kg_data, pub_data)
    set_cache(cache_key, result, ttl=600)
    return result


def _build_education_content(disease: str, kg_data: dict, pub_data: dict) -> dict:
    """构建疾病教育内容。"""
    entities = kg_data.get("data", kg_data.get("entities", []))
    papers = pub_data.get("data", pub_data.get("papers", []))

    return {
        "disease": disease,
        "overview": f"{disease}是一种需要长期管理的慢性疾病，及时了解相关信息对治疗至关重要。",
        "treatment_guidelines": [
            {
                "title": f"{disease}标准治疗方案",
                "source": "临床指南",
                "summary": f"针对{disease}的标准化治疗流程和用药建议。",
            }
        ],
        "recommended_articles": [
            {
                "title": paper.get("title", ""),
                "source": paper.get("source", paper.get("journal", "")),
                "abstract": paper.get("abstract", paper.get("summary", "")),
            }
            for paper in papers[:5]
        ],
        "related_entities": [
            {
                "name": e.get("name", ""),
                "type": e.get("entity_type", e.get("type", "")),
                "relation": e.get("relation", "related"),
            }
            for e in entities[:5]
        ],
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


async def get_recommended_content(patient_id: str) -> dict:
    """个性化推荐内容。

    根据患者 ID 获取个性化推荐的教育内容，
    结合患者病情、治疗阶段和偏好进行匹配。

    Args:
        patient_id: 患者唯一标识。

    Returns:
        包含个性化推荐内容的字典。
    """
    cache_key = f"edu:recommend:{patient_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        profile_resp = await client.get(f"{CLOUD_API}/kg/entities/{patient_id}")
        profile = {}
        if profile_resp.status_code == 200:
            pdata = profile_resp.json()
            profile = pdata.get("data", pdata.get("entity", {}))

    result = _build_recommended_content(patient_id, profile)
    set_cache(cache_key, result, ttl=600)
    return result


def _build_recommended_content(patient_id: str, profile: dict) -> dict:
    """构建个性化推荐内容。"""
    props = profile.get("properties", {})
    conditions = props.get("conditions", [])
    if isinstance(conditions, str):
        conditions = [conditions]

    return {
        "patient_id": patient_id,
        "recommendations": [
            {
                "content_id": f"CONT-{i + 1:04d}",
                "title": f"{cond}患者教育手册",
                "type": "article",
                "relevance": 0.95 - i * 0.1,
                "reason": f"基于您的{cond}诊断",
            }
            for i, cond in enumerate(conditions[:5])
        ]
        or [
            {
                "content_id": "CONT-0001",
                "title": "慢性病自我管理指南",
                "type": "article",
                "relevance": 0.85,
                "reason": "基于您的健康档案",
            }
        ],
        "total_recommendations": max(len(conditions), 1),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


async def push_content(content_id: str, patient_ids: list[str]) -> dict:
    """推送内容。

    将指定教育内容推送给目标患者群体。
    调用 Cloud 通知服务发送推送。

    Args:
        content_id: 内容标识。
        patient_ids: 目标患者 ID 列表。

    Returns:
        推送结果的字典。
    """
    async with httpx.AsyncClient() as client:
        notif_resp = await client.post(
            f"{CLOUD_API}/notifications/send",
            json={
                "content_id": content_id,
                "recipients": patient_ids,
                "channel": "education",
            },
        )

    return {
        "content_id": content_id,
        "total_patients": len(patient_ids),
        "pushed": notif_resp.status_code == 200,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
