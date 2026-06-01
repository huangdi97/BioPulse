import httpx

from management.app.database import get_cache, set_cache

CLOUD_API = "http://localhost:8000"
CACHE_TTL = 60


async def get_team_stats(team_id: int) -> dict:
    """获取团队统计信息。

    调用 /teams/{id}/members 和 /board/stats 聚合。
    """
    cache_key = f"manager:team_stats:{team_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        r1 = await client.get(f"{CLOUD_API}/teams/{team_id}/members")
        r2 = await client.get(f"{CLOUD_API}/board/stats")

    result = {
        "members": r1.json() if r1.status_code == 200 else {},
        "board_stats": r2.json() if r2.status_code == 200 else {},
    }
    set_cache(cache_key, result, ttl=CACHE_TTL)
    return result


async def get_team_members(team_id: int) -> dict:
    """获取团队成员列表。"""
    cache_key = f"manager:team_members:{team_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{CLOUD_API}/teams/{team_id}/members")

    result = resp.json() if resp.status_code == 200 else {}
    set_cache(cache_key, result, ttl=CACHE_TTL)
    return result


async def get_team_compliance(team_id: int) -> dict:
    """获取团队合规数据。"""
    cache_key = f"manager:team_compliance:{team_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{CLOUD_API}/compliance-v2/enforce/stats")

    result = resp.json() if resp.status_code == 200 else {}
    set_cache(cache_key, result, ttl=CACHE_TTL)
    return result


async def get_team_performance(team_id: int) -> dict:
    """获取团队绩效数据。"""
    cache_key = f"manager:team_performance:{team_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{CLOUD_API}/board/stats")

    result = resp.json() if resp.status_code == 200 else {}
    set_cache(cache_key, result, ttl=CACHE_TTL)
    return result
