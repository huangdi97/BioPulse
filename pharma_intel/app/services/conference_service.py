"""学术会议追踪服务。"""

import httpx

from pharma_intel.app.database import get_cache, set_cache
from pharma_intel.app.services.conference_aggregator import analyze_conference_trends
from pharma_intel.app.services.conference_parser import MOCK_CONFERENCES, get_conference_detail
from shared.app_settings import settings

CLOUD_API = settings.cloud_api_base


async def get_upcoming_conferences(limit: int = 10) -> list[dict]:
    cache_key = f"conferences:upcoming:{limit}"
    cached = get_cache(cache_key)
    if cached:
        return cached
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{CLOUD_API}/pubmed/search", json={"query": "clinical trial conference 2026", "limit": 20})
        if resp.status_code == 200:
            data = resp.json()
            papers = data.get("data", data.get("papers", []))
    conferences = MOCK_CONFERENCES[:limit]
    if papers:
        for conf in conferences:
            conf["related_papers"] = [p.get("title", "") for p in papers[:5]] if papers else []
    set_cache(cache_key, conferences, ttl=1800)
    return conferences
