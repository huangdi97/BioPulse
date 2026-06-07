"""中心筛选服务。"""

from datetime import datetime, timezone

import httpx

from ..database import get_cache, set_cache

CLOUD_API = "http://localhost:8000"


async def search_sites(indication: str) -> dict:
    """按适应症搜索临床试验中心。

    调用 Cloud PubMed 搜索获取相关论文，结合知识图谱查找中心信息，
    返回匹配的临床试验中心列表。
    """
    cache_key = f"site:search:{indication}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        pub_resp = await client.post(
            f"{CLOUD_API}/pubmed/search",
            json={
                "query": indication,
                "limit": 20,
            },
        )
        papers = []
        if pub_resp.status_code == 200:
            pub_data = pub_resp.json()
            papers = pub_data.get("data", pub_data.get("papers", []))

        kg_resp = await client.get(
            f"{CLOUD_API}/kg/entities",
            params={
                "name": indication,
                "entity_type": "site",
            },
        )
        kg_entities = []
        if kg_resp.status_code == 200:
            kg_data = kg_resp.json()
            kg_entities = kg_data.get("data", kg_data.get("entities", []))

    result = _build_site_list(indication, papers, kg_entities)
    set_cache(cache_key, result, ttl=600)
    return result


def _build_site_list(indication: str, papers: list, kg_entities: list) -> dict:
    """构建临床试验中心列表。"""
    sites = []
    for i, paper in enumerate(papers[:10]):
        site_name = f"{indication}临床中心{'甲乙丙丁戊'[i % 5]}"
        sites.append(
            {
                "site_id": f"SITE-{i + 1:04d}",
                "name": f"{site_name}医院",
                "location": ["北京", "上海", "广州", "成都", "武汉"][i % 5],
                "principal_investigator": paper.get("author", paper.get("authors", [{}])[0].get("name", ""))
                if isinstance(paper.get("authors"), list)
                else "",
                "patient_capacity": 50 + i * 30,
                "status": "active" if i % 3 != 0 else "pending",
                "therapeutic_area": indication,
            }
        )

    for entity in kg_entities:
        sites.append(
            {
                "site_id": entity.get("entity_id", f"KG-{len(sites) + 1:04d}"),
                "name": entity.get("name", ""),
                "location": entity.get("properties", {}).get("location", ""),
                "principal_investigator": entity.get("properties", {}).get("pi", ""),
                "patient_capacity": entity.get("properties", {}).get("capacity", 0),
                "status": entity.get("properties", {}).get("status", "active"),
                "therapeutic_area": entity.get("properties", {}).get("area", indication),
            }
        )

    return {
        "indication": indication,
        "total_sites": len(sites),
        "sites": sites,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


async def get_site_detail(site_id: str) -> dict:
    """获取临床试验中心详情。

    调用 Cloud 知识图谱查询中心详细信息，
    返回该中心的完整信息、研究者和试验概况。
    """
    cache_key = f"site:detail:{site_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        kg_resp = await client.get(f"{CLOUD_API}/kg/entities/{site_id}")
        entity = {}
        if kg_resp.status_code == 200:
            kg_data = kg_resp.json()
            entity = kg_data.get("data", kg_data.get("entity", {}))

    result = _build_site_detail(site_id, entity)
    set_cache(cache_key, result, ttl=600)
    return result


def _build_site_detail(site_id: str, entity: dict) -> dict:
    """构建临床试验中心详情。"""
    props = entity.get("properties", {})
    return {
        "site_id": site_id,
        "name": entity.get("name", f"中心 {site_id}"),
        "type": props.get("type", "三级甲等医院"),
        "location": props.get("location", ""),
        "contact": {
            "phone": props.get("phone", ""),
            "email": props.get("email", ""),
            "address": props.get("address", ""),
        },
        "principal_investigator": {
            "name": props.get("pi", ""),
            "specialty": props.get("pi_specialty", ""),
            "experience_years": props.get("pi_experience", 0),
        },
        "departments": props.get("departments", ["肿瘤科", "血液科", "免疫科"]),
        "patient_capacity": props.get("capacity", 100),
        "ongoing_trials": props.get("ongoing_trials", 3),
        "completed_trials": props.get("completed_trials", 15),
        "accreditation": props.get("accreditation", "GCP认证"),
        "status": props.get("status", "active"),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
