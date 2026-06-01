import httpx

from management.app.database import get_cache, set_cache

CLOUD_API = "http://localhost:8000"
CACHE_TTL = 60


async def get_my_profile(user_id: int) -> dict:
    """获取个人资料。"""
    cache_key = f"employee:profile:{user_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{CLOUD_API}/users/{user_id}")

    result = resp.json() if resp.status_code == 200 else {}
    set_cache(cache_key, result, ttl=CACHE_TTL)
    return result


async def get_my_tasks(user_id: int) -> dict:
    """获取个人任务列表。"""
    cache_key = f"employee:tasks:{user_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{CLOUD_API}/tasks", params={"user_id": user_id})

    result = resp.json() if resp.status_code == 200 else {}
    set_cache(cache_key, result, ttl=CACHE_TTL)
    return result


async def get_my_compliance(user_id: int) -> dict:
    """获取个人合规数据。"""
    cache_key = f"employee:compliance:{user_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{CLOUD_API}/compliance-v2/enforce/stats")

    result = resp.json() if resp.status_code == 200 else {}
    set_cache(cache_key, result, ttl=CACHE_TTL)
    return result


async def get_my_performance(user_id: int) -> dict:
    """获取个人绩效数据。"""
    cache_key = f"employee:performance:{user_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{CLOUD_API}/board/stats")

    result = resp.json() if resp.status_code == 200 else {}
    set_cache(cache_key, result, ttl=CACHE_TTL)
    return result


async def get_my_trend(user_id: int) -> dict:
    """获取个人趋势数据。"""
    cache_key = f"employee:trend:{user_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{CLOUD_API}/dashboard/analytics")

    result = resp.json() if resp.status_code == 200 else {}
    set_cache(cache_key, result, ttl=CACHE_TTL)
    return result
