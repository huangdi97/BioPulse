"""竞品情报服务。"""

from datetime import datetime, timezone

import httpx
from pharma_intel.app.database import get_cache, set_cache

CLOUD_API = "http://localhost:8000"


async def get_competitor_intel(company_name: str) -> dict:
    """获取指定竞争对手的综合情报。

    调用 Cloud Market Intel API 获取该公司相关新闻，
    调用 Cloud PubMed API 获取该公司论文动态，
    聚合返回新闻摘要、论文活动和近期事件。
    """
    cache_key = f"competitor:intel:{company_name}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        news_resp = await client.get(
            f"{CLOUD_API}/market-intel/items",
            params={
                "keyword": company_name,
                "limit": 20,
            },
        )
        news_items = []
        if news_resp.status_code == 200:
            data = news_resp.json()
            news_items = data.get("data", data.get("items", []))

        pub_resp = await client.post(
            f"{CLOUD_API}/pubmed/search",
            json={
                "query": company_name,
                "limit": 50,
            },
        )
        papers = []
        if pub_resp.status_code == 200:
            data = pub_resp.json()
            papers = data.get("data", data.get("papers", []))

    result = _aggregate_competitor_intel(company_name, news_items, papers)
    set_cache(cache_key, result, ttl=1800)
    return result


def _aggregate_competitor_intel(company: str, news: list, papers: list) -> dict:
    """聚合竞品情报。"""
    recent_events = []
    for item in news:
        title = item.get("title") or item.get("headline") or ""
        date = item.get("date") or item.get("published_at") or ""
        url = item.get("url") or ""
        recent_events.append(
            {
                "title": title,
                "date": date,
                "url": url,
                "source": item.get("source", item.get("source_type", "")),
            }
        )

    paper_count = len(papers)
    paper_years = []
    for p in papers:
        year = p.get("year") or p.get("Year") or p.get("pub_date", "")[:4]
        if year and year.isdigit():
            paper_years.append(int(year))

    return {
        "company": company,
        "news_summary": {
            "total_news": len(news),
            "recent_headlines": [e["title"] for e in recent_events[:5]],
        },
        "paper_activity": {
            "total_papers": paper_count,
            "active_years": sorted(set(paper_years)) if paper_years else [],
        },
        "recent_events": recent_events[:10],
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


async def get_market_news(limit: int = 10) -> dict:
    """获取行业新闻动态。

    调用 Cloud Market Intel API 获取最新的行业新闻和动态。
    """
    cache_key = f"market:news:limit:{limit}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{CLOUD_API}/market-intel/items",
            params={
                "limit": limit,
            },
        )
        items = []
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("data", data.get("items", []))

    news_list = []
    for item in items:
        news_list.append(
            {
                "title": item.get("title") or item.get("headline") or "",
                "summary": item.get("summary") or item.get("content", "")[:200],
                "date": item.get("date") or item.get("published_at") or "",
                "source": item.get("source", item.get("source_type", "")),
                "url": item.get("url") or "",
                "impact_level": item.get("impact_level") or item.get("ImpactLevel", ""),
            }
        )

    result = {
        "total_news": len(news_list),
        "news": news_list,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    set_cache(cache_key, result, ttl=1800)
    return result
