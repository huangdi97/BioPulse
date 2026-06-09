"""管理端竞品看板 API。"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from starlette import status

from shared.app_settings import settings
from shared.base import success

router = APIRouter(prefix="/api/competitor", tags=["竞品看板"])

CLOUD_API = settings.cloud_api_base
SEVERITY_RANK = {"high": 3, "medium": 2, "low": 1}


async def _cloud_get(path: str) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(f"{CLOUD_API}{path}")
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Cloud competitor service unavailable: {exc}",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cloud competitor service returned invalid JSON",
        ) from exc
    if not isinstance(payload, dict):
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail="Cloud competitor payload is invalid")
    return payload


async def _load_products() -> list[dict[str, Any]]:
    payload = await _cloud_get("/api/competitor/products")
    products = payload.get("data")
    if not isinstance(products, list):
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail="Cloud competitor products payload is invalid")
    return [item for item in products if isinstance(item, dict)]


async def _price_trend(product_id: str, days: int = 7) -> list[dict[str, Any]]:
    payload = await _cloud_get(f"/api/competitor/price/trend?product_id={product_id}&days={days}")
    data = payload.get("data") or {}
    trend = data.get("trend") if isinstance(data, dict) else None
    return trend if isinstance(trend, list) else []


def _category_distribution(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(str(item.get("category") or "unknown") for item in products)
    return [{"category": category, "count": count} for category, count in counts.items()]


def _aggregate_price_trends(price_trends: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    by_date: dict[str, list[float]] = defaultdict(list)
    for trend in price_trends.values():
        for point in trend:
            point_date = point.get("date")
            price = point.get("price")
            if point_date and isinstance(price, (int, float)):
                by_date[str(point_date)].append(float(price))
    return [
        {"date": point_date, "avg_price": round(sum(values) / len(values), 2), "sample_count": len(values)}
        for point_date, values in sorted(by_date.items())
    ]


def _region_comparison(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    regions: dict[str, dict[str, Any]] = {}
    for product in products:
        for region in product.get("province_coverage") or ["uncovered"]:
            item = regions.setdefault(
                region,
                {
                    "region": region,
                    "product_count": 0,
                    "active_count": 0,
                    "watchlist_count": 0,
                    "companies": set(),
                    "products": [],
                },
            )
            item["product_count"] += 1
            if product.get("status") == "active":
                item["active_count"] += 1
            if product.get("status") == "watchlist":
                item["watchlist_count"] += 1
            item["companies"].add(product.get("company") or "unknown")
            item["products"].append({"id": product.get("id"), "name": product.get("name")})

    rows = []
    for item in regions.values():
        rows.append(
            {
                **item,
                "company_count": len(item["companies"]),
                "companies": sorted(item["companies"]),
                "risk_level": "medium" if item["watchlist_count"] else "low",
            }
        )
    return sorted(rows, key=lambda item: (item["watchlist_count"], item["product_count"]), reverse=True)


def _alert_from_price_trend(product: dict[str, Any], trend: list[dict[str, Any]]) -> dict[str, Any] | None:
    if len(trend) < 2:
        return None
    first_price = float(trend[0].get("price") or 0)
    latest_price = float(trend[-1].get("price") or 0)
    if not first_price:
        return None
    change_pct = round((latest_price - first_price) / first_price * 100, 2)
    if abs(change_pct) < 1.0 and product.get("status") != "watchlist":
        return None
    severity = "high" if abs(change_pct) >= 3 or product.get("status") == "watchlist" else "medium"
    return {
        "id": f"alert-{product.get('id')}-price",
        "product_id": product.get("id"),
        "product_name": product.get("name"),
        "company": product.get("company"),
        "severity": severity,
        "type": "price_or_watchlist",
        "message": f"近7天价格指数变化{change_pct}%，状态为{product.get('status')}",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/global-trend", summary="全局竞品趋势", tags=["竞品看板"])
async def global_trend():
    products = await _load_products()
    price_trends = {str(product.get("id")): await _price_trend(str(product.get("id")), days=7) for product in products if product.get("id")}
    status_counts = Counter(str(item.get("status") or "unknown") for item in products)
    data = {
        "window_days": 7,
        "tracked_product_count": len(products),
        "active_count": status_counts.get("active", 0),
        "watchlist_count": status_counts.get("watchlist", 0),
        "category_distribution": _category_distribution(products),
        "avg_price_trend": _aggregate_price_trends(price_trends),
        "generated_at": date.today().isoformat(),
    }
    return success(data=data)


@router.get("/region-comparison", summary="区域对比", tags=["竞品看板"])
async def region_comparison():
    products = await _load_products()
    return success(data={"regions": _region_comparison(products), "tracked_product_count": len(products)})


@router.get("/alert-list", summary="预警列表", tags=["竞品看板"])
async def alert_list():
    products = await _load_products()
    alerts = []
    for product in products:
        if not product.get("id"):
            continue
        alert = _alert_from_price_trend(product, await _price_trend(str(product["id"]), days=7))
        if alert:
            alerts.append(alert)
    alerts.sort(key=lambda item: (item["created_at"], SEVERITY_RANK.get(item["severity"], 0)), reverse=True)
    return success(data={"alerts": alerts, "total": len(alerts)})
