"""管线竞争分析服务。"""

from datetime import datetime, timezone

import httpx

from pharma_intel.app.database import get_cache, set_cache

CLOUD_API = "http://localhost:8000"

_PHASE_MAP = {
    "phase1": "I期",
    "phase i": "I期",
    "phase 1": "I期",
    "phase2": "II期",
    "phase ii": "II期",
    "phase 2": "II期",
    "phase3": "III期",
    "phase iii": "III期",
    "phase 3": "III期",
    "launched": "上市",
    "approved": "上市",
    "上市": "上市",
    "preclinical": "临床前",
    "discovery": "发现",
}


async def analyze_pipeline(company: str, therapeutic_area: str = "") -> dict:
    """分析指定公司在特定治疗领域的管线。

    调用 Cloud PubMed API 和 KG API 聚合管线数据，返回管线总数、
    分期分布、适应症分布及 TOP5 竞争对手。
    """
    cache_key = f"pipeline:{company}:{therapeutic_area}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        pub_resp = await client.post(
            f"{CLOUD_API}/pubmed/search",
            json={
                "query": f"{company} {therapeutic_area}" if therapeutic_area else company,
                "limit": 100,
            },
        )
        papers = []
        if pub_resp.status_code == 200:
            data = pub_resp.json()
            papers = data.get("data", data.get("papers", []))

        kg_resp = await client.get(
            f"{CLOUD_API}/kg/entities",
            params={
                "name": company,
                "entity_type": "pipeline",
            },
        )
        pipelines = []
        if kg_resp.status_code == 200:
            data = kg_resp.json()
            pipelines = data.get("data", data.get("entities", []))

    result = _aggregate_pipeline(company, therapeutic_area, papers, pipelines)
    set_cache(cache_key, result, ttl=1800)
    return result


def _aggregate_pipeline(company: str, therapeutic_area: str, papers: list, pipelines: list) -> dict:
    """聚合管线分析结果。"""
    phase_dist = {"I期": 0, "II期": 0, "III期": 0, "上市": 0}
    indication_dist = {}
    competitors_raw = {}

    for p in pipelines:
        phase = (p.get("phase") or p.get("Phase") or "").lower()
        mapped = _PHASE_MAP.get(phase)
        if mapped in phase_dist:
            phase_dist[mapped] += 1

        ind = p.get("indication") or p.get("Indication") or ""
        if ind:
            indication_dist[ind] = indication_dist.get(ind, 0) + 1

        org = p.get("organization") or p.get("Organization") or p.get("company") or ""
        if org and org.lower() != company.lower():
            competitors_raw[org] = competitors_raw.get(org, 0) + 1

    for p in papers:
        org = p.get("organization") or p.get("affiliation") or ""
        if org and org.lower() != company.lower():
            org_short = org.split(",")[0].strip()
            if org_short:
                competitors_raw[org_short] = competitors_raw.get(org_short, 0) + 1

    sorted_competitors = sorted(competitors_raw.items(), key=lambda x: -x[1])
    top5 = [{"name": name, "count": cnt} for name, cnt in sorted_competitors[:5]]

    return {
        "company": company,
        "therapeutic_area": therapeutic_area or "all",
        "total_pipelines": len(pipelines),
        "phase_distribution": phase_dist,
        "indication_distribution": indication_dist,
        "competitors_top5": top5,
        "total_related_papers": len(papers),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


async def search_pipeline_by_indication(indication: str) -> dict:
    """按适应症搜索在研管线。

    调用 Cloud PubMed API 和 KG API，返回匹配该适应症的管线列表。
    """
    cache_key = f"pipeline:indication:{indication}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        pub_resp = await client.post(
            f"{CLOUD_API}/pubmed/search",
            json={
                "query": indication,
                "limit": 50,
            },
        )
        papers = []
        if pub_resp.status_code == 200:
            data = pub_resp.json()
            papers = data.get("data", data.get("papers", []))

        kg_resp = await client.get(
            f"{CLOUD_API}/kg/entities",
            params={
                "entity_type": "pipeline",
                "indication": indication,
            },
        )
        pipelines = []
        if kg_resp.status_code == 200:
            data = kg_resp.json()
            pipelines = data.get("data", data.get("entities", []))

    result = {
        "indication": indication,
        "pipelines": pipelines,
        "total_pipelines": len(pipelines),
        "total_related_papers": len(papers),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    set_cache(cache_key, result, ttl=1800)
    return result
