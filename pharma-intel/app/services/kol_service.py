"""KOL 学术影响力追踪服务。"""

from datetime import datetime, timezone

import httpx
from pharma_intel.app.database import get_cache, set_cache

CLOUD_API = "http://localhost:8000"


async def search_kol(name: str, institution: str = "") -> dict:
    """搜索 KOL 学术信息。

    调用 Cloud PubMed API 获取论文列表 → 聚合统计 → 返回 KOL 画像。
    """
    cache_key = f"kol:{name}:{institution}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        # 调用 Cloud 的 pubmed 搜索
        resp = await client.post(
            f"{CLOUD_API}/pubmed/search",
            json={
                "query": f"{name} {institution}" if institution else name,
                "limit": 50,
            },
        )

        papers = []
        if resp.status_code == 200:
            data = resp.json()
            papers = data.get("data", data.get("papers", []))

    result = _aggregate_kol_profile(name, papers)
    set_cache(cache_key, result, ttl=1800)
    return result


def _aggregate_kol_profile(name: str, papers: list) -> dict:
    """聚合 KOL 画像数据。"""
    total_papers = len(papers)
    # 提取研究领域
    keywords = set()
    years = []
    journals = set()

    for p in papers:
        title = (p.get("title") or p.get("Title") or "").lower()
        # 简单关键词提取
        for kw in [
            "cancer",
            "immunology",
            "neuroscience",
            "cardiology",
            "oncology",
            "diabetes",
            "rare disease",
            "gene therapy",
        ]:
            if kw in title:
                keywords.add(kw)
        year = p.get("year") or p.get("Year") or p.get("pub_date", "")[:4]
        if year and year.isdigit():
            years.append(int(year))
        journal = p.get("journal") or p.get("Journal") or ""
        if journal:
            journals.add(journal)

    return {
        "name": name,
        "total_papers": total_papers,
        "research_areas": list(keywords) or ["general medicine"],
        "pub_years": sorted(set(years)) if years else [],
        "active_journals": list(journals)[:5],
        "h_index_estimate": _estimate_h_index(papers),
        "recent_activity": years[-5:] if len(years) >= 5 else years,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


def _estimate_h_index(papers: list) -> int:
    """粗略估计 H 指数（基于论文数）。"""
    n = len(papers)
    if n >= 50:
        return 25
    if n >= 30:
        return 15
    if n >= 10:
        return 8
    if n >= 5:
        return 3
    return 1
