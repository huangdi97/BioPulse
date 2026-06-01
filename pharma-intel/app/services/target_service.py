"""靶点研究监控服务。"""

from collections import Counter
from datetime import datetime, timezone

import httpx
from pharma_intel.app.database import get_cache, set_cache

CLOUD_API = "http://localhost:8000"


async def analyze_target(target_name: str) -> dict:
    """分析指定靶点的学术研究态势。

    调用 Cloud PubMed API 搜索靶点相关论文，聚合返回论文总数、
    月度发文趋势、TOP10 研究机构及相关公司。
    """
    cache_key = f"target:{target_name}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{CLOUD_API}/pubmed/search",
            json={
                "query": target_name,
                "limit": 200,
            },
        )
        papers = []
        if resp.status_code == 200:
            data = resp.json()
            papers = data.get("data", data.get("papers", []))

    result = _aggregate_target(target_name, papers)
    set_cache(cache_key, result, ttl=1800)
    return result


def _aggregate_target(name: str, papers: list) -> dict:
    """聚合靶点分析信息。"""
    monthly_counter: Counter = Counter()
    institution_counter: Counter = Counter()
    company_set: set = set()
    _COMPANY_KEYWORDS = [
        "inc",
        "ltd",
        "limited",
        "corp",
        "corporation",
        "pharma",
        "biotech",
        "therapeutics",
        "laboratories",
    ]

    for p in papers:
        date_str = (p.get("pub_date") or p.get("PubDate") or "").strip()
        if len(date_str) >= 7:
            month_key = date_str[:7]
            monthly_counter[month_key] += 1
        elif len(date_str) >= 4:
            month_key = date_str[:4]
            monthly_counter[month_key] += 1

        affil = p.get("affiliation") or p.get("Affiliation") or ""
        parts = [a.strip() for a in affil.split(",") if a.strip()]
        if parts:
            inst = ", ".join(parts[:2])
            institution_counter[inst] += 1

            for part in parts:
                lower = part.lower()
                if any(kw in lower for kw in _COMPANY_KEYWORDS):
                    company_set.add(part.strip())

    monthly_trend = sorted(
        [{"month": k, "count": v} for k, v in monthly_counter.items()],
        key=lambda x: x["month"],
    )
    top_institutions = [{"name": name, "count": cnt} for name, cnt in institution_counter.most_common(10)]

    return {
        "target_name": name,
        "total_papers": len(papers),
        "monthly_trend": monthly_trend,
        "top_institutions": top_institutions,
        "related_companies": sorted(company_set),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


async def trending_targets(limit: int = 10) -> dict:
    """获取近期活跃靶点列表。

    通过分析缓存的靶点数据，返回发文量最多的靶点。
    当前简化版本调用 PubMed 搜索活跃研究方向。
    """
    cache_key = "trending_targets"
    cached = get_cache(cache_key)
    if cached:
        return cached

    queries = [
        "PD-1",
        "PD-L1",
        "EGFR",
        "HER2",
        "CD3",
        "CD19",
        "CTLA-4",
        "JAK",
        "BTK",
        "KRAS",
        "BCMA",
        "GPC3",
        "CLDN18.2",
        "TROP2",
    ]
    async with httpx.AsyncClient() as client:
        results = []
        for q in queries[:limit]:
            resp = await client.post(
                f"{CLOUD_API}/pubmed/search",
                json={
                    "query": q,
                    "limit": 10,
                },
            )
            count = 0
            if resp.status_code == 200:
                data = resp.json()
                count = len(data.get("data", data.get("papers", [])))
            results.append({"target": q, "recent_papers": count})

    results.sort(key=lambda x: -x["recent_papers"])
    result = {
        "trending_targets": results[:limit],
        "total": len(results[:limit]),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    set_cache(cache_key, result, ttl=1800)
    return result
