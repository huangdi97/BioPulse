import httpx

from management.app.database import get_cache, set_cache

CLOUD_API = "http://localhost:8000"
CACHE_TTL = 60


async def get_summary() -> dict:
    """聚合全局概览数据。

    调用 analytics、teams/list、compliance stats 三个接口聚合返回。
    """
    cache_key = "president:summary"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        r1 = await client.get(f"{CLOUD_API}/dashboard/analytics")
        r2 = await client.get(f"{CLOUD_API}/teams/list")
        r3 = await client.get(f"{CLOUD_API}/compliance-v2/enforce/stats")

    result = {
        "analytics": r1.json() if r1.status_code == 200 else {},
        "teams": r2.json() if r2.status_code == 200 else {},
        "compliance_stats": r3.json() if r3.status_code == 200 else {},
    }
    set_cache(cache_key, result, ttl=CACHE_TTL)
    return result


async def get_compliance_overview() -> dict:
    """获取合规概览数据。"""
    cache_key = "president:compliance_overview"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{CLOUD_API}/compliance-v2/enforce/stats")

    result = resp.json() if resp.status_code == 200 else {}
    set_cache(cache_key, result, ttl=CACHE_TTL)
    return result


async def get_team_rankings() -> dict:
    """获取团队排名数据。"""
    cache_key = "president:team_rankings"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{CLOUD_API}/teams/list")

    result = resp.json() if resp.status_code == 200 else {}
    set_cache(cache_key, result, ttl=CACHE_TTL)
    return result


async def get_trend_report() -> dict:
    """获取趋势报告数据。"""
    cache_key = "president:trend_report"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{CLOUD_API}/dashboard/analytics")

    result = resp.json() if resp.status_code == 200 else {}
    set_cache(cache_key, result, ttl=CACHE_TTL)
    return result
