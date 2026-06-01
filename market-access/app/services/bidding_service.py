"""招标价格监控服务。"""

import httpx
from datetime import datetime, timezone
from market_access.app.database import get_cache, set_cache

CLOUD_API = "http://localhost:8000"


async def get_bidding_data(drug_name: str) -> dict:
    """查询药品招标信息。

    调用 Cloud Market Intel API 获取目标药品的招标/新闻情报，
    返回招标相关条目的标题、摘要、来源和影响级别。
    """
    cache_key = f"bidding:data:{drug_name}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{CLOUD_API}/market-intel/items", params={
            "keyword": drug_name,
            "limit": 30,
        })
        items = []
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("data", data.get("items", []))

    bidding_items = []
    for item in items:
        bidding_items.append({
            "title": item.get("title", ""),
            "summary": item.get("summary", ""),
            "source": item.get("source_name", item.get("source", "")),
            "impact_level": item.get("impact_level", ""),
            "date": item.get("collected_at", item.get("date", "")),
        })

    result = {
        "drug_name": drug_name,
        "total_bidding_news": len(bidding_items),
        "bidding_news": bidding_items,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    set_cache(cache_key, result, ttl=300)
    return result


async def get_price_trend(drug_name: str) -> dict:
    """获取药品价格趋势。

    调用 Cloud Market Intel API 获取相关情报后，
    模拟生成近 6 个月的价格趋势数据。
    """
    cache_key = f"bidding:trend:{drug_name}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{CLOUD_API}/market-intel/items", params={
            "keyword": drug_name,
            "limit": 10,
        })
        items = []
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("data", data.get("items", []))

    item_count = len(items)
    result = _simulate_price_trend(drug_name, item_count)
    set_cache(cache_key, result, ttl=300)
    return result


def _simulate_price_trend(drug_name: str, item_count: int) -> dict:
    """模拟生成近 6 个月价格趋势。"""
    base_price = 50.0 + (item_count * 3.5)
    months = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]
    trend = []
    for i, m in enumerate(months):
        fluctuation = (i - 2.5) * 1.2 + (item_count % 5) * 0.5
        price = round(base_price + fluctuation, 2)
        trend.append({"month": m, "price": price})

    return {
        "drug_name": drug_name,
        "currency": "CNY",
        "trend": trend,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


async def get_province_prices(drug_name: str) -> dict:
    """查询各省药品中标价。

    调用 Cloud Market Intel API 获取相关情报后，
    模拟生成各省中标价格数据。
    """
    cache_key = f"bidding:province:{drug_name}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{CLOUD_API}/market-intel/items", params={
            "keyword": drug_name,
            "limit": 15,
        })
        items = []
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("data", data.get("items", []))

    item_count = len(items)
    result = _simulate_province_prices(drug_name, item_count)
    set_cache(cache_key, result, ttl=300)
    return result


def _simulate_province_prices(drug_name: str, item_count: int) -> dict:
    """模拟生成各省中标价。"""
    provinces = [
        "北京", "上海", "广东", "江苏", "浙江", "山东",
        "河南", "四川", "湖北", "湖南", "河北", "福建",
    ]
    base = 100.0 + item_count * 2.0
    prices = []
    for i, p in enumerate(provinces):
        adj = base + (i % 7) * 3.0 - (item_count % 3) * 2.0
        prices.append({
            "province": p,
            "bid_price": round(adj, 2),
            "unit": "元/盒",
        })

    return {
        "drug_name": drug_name,
        "prices": prices,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
