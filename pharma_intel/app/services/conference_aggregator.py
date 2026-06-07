"""学术会议热点趋势聚合分析。"""

from datetime import datetime, timezone

from pharma_intel.app.database import get_cache, set_cache
from pharma_intel.app.services.conference_parser import MOCK_CONFERENCES


async def analyze_conference_trends(months: int = 6) -> dict:
    cache_key = f"conference:trends:{months}"
    cached = get_cache(cache_key)
    if cached:
        return cached
    topic_counter: dict[str, int] = {}
    for conf in MOCK_CONFERENCES:
        for topic in conf["hot_topics"]:
            topic_counter[topic] = topic_counter.get(topic, 0) + 1
    trending = [
        {"topic": topic, "mentions": count, "conferences_covered": count} for topic, count in sorted(topic_counter.items(), key=lambda x: -x[1])
    ]
    result = {
        "trending_topics": trending,
        "analysis_window_months": months,
        "total_conferences_analyzed": len(MOCK_CONFERENCES),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    set_cache(cache_key, result, ttl=1800)
    return result
