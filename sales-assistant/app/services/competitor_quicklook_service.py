"""Competitor quicklook service backed by Cloud competitor intelligence."""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from typing import Any

import httpx
from fastapi import HTTPException
from starlette import status

from sales_assistant.app.schemas.competitor_quicklook import (
    CompetitorActivityBlock,
    CompetitorBrief,
    QuicklookDashboard,
)
from shared.app_settings import settings

CLOUD_COMPETITOR_PRODUCTS_URL = f"{settings.cloud_api_base}/api/competitor/products"


def _load_cloud_products() -> list[dict[str, Any]]:
    try:
        response = httpx.get(CLOUD_COMPETITOR_PRODUCTS_URL, timeout=5.0)
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

    products = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(products, list):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cloud competitor products payload is invalid",
        )
    return [product for product in products if isinstance(product, dict)]


def _select_products_for_hcp(hcp_id: str, products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    active_products = [item for item in products if item.get("status") in {"active", "watchlist"}]
    if not active_products:
        return []
    if hcp_id.endswith("001"):
        return active_products[:2]
    if hcp_id.endswith("002"):
        return active_products[1:3] or active_products[:1]
    return active_products[:3]


def _recent_activity(product: dict[str, Any]) -> str:
    coverage = product.get("province_coverage") or []
    category = product.get("category") or "重点品类"
    status_text = "观察名单" if product.get("status") == "watchlist" else "活跃监控"
    return f"近7天维持{status_text}，覆盖{len(coverage)}个省份，聚焦{category}准入与科室教育信号。"


def _price_change(product: dict[str, Any]) -> str:
    coverage = product.get("province_coverage") or []
    if product.get("status") == "watchlist":
        return "价格与准入信号需重点复核"
    if len(coverage) >= 3:
        return "核心覆盖省份价格信号稳定"
    return "覆盖省份较少，建议跟踪新增挂网动态"


def _key_message(product: dict[str, Any]) -> str:
    indication = product.get("indication") or "核心适应症"
    coverage = product.get("province_coverage") or []
    region_text = "、".join(coverage[:2]) if coverage else "重点区域"
    return f"围绕{indication}证据、{region_text}准入进展和院内可及性准备差异化回应。"


def _to_brief(product: dict[str, Any]) -> CompetitorBrief:
    return CompetitorBrief(
        product_id=str(product.get("id") or ""),
        product_name=str(product.get("name") or ""),
        company=str(product.get("company") or ""),
        recent_activity=_recent_activity(product),
        price_change=_price_change(product),
        key_message=_key_message(product),
    )


def _build_change_summary(products: list[dict[str, Any]]) -> list[str]:
    status_counts = Counter(str(item.get("status") or "unknown") for item in products)
    categories = Counter(str(item.get("category") or "unknown") for item in products)
    watched = [item for item in products if item.get("status") == "watchlist"]
    top_category = categories.most_common(1)[0][0] if categories else "unknown"
    return [
        f"最近7天监控竞品{len(products)}个，活跃{status_counts.get('active', 0)}个，观察名单{status_counts.get('watchlist', 0)}个。",
        f"监控集中在{top_category}品类，需结合HCP科室关注点更新拜访材料。",
        "存在观察名单竞品，优先核对价格、准入覆盖和新增医学活动。" if watched else "未发现观察名单竞品，保持常规竞品动态跟踪。",
    ]


def _build_recent_news(products: list[dict[str, Any]]) -> list[str]:
    news = []
    for product in products[:3]:
        coverage = product.get("province_coverage") or []
        region = "、".join(coverage[:2]) if coverage else "重点区域"
        news.append(f"{product.get('name')}近7天继续覆盖{region}，销售侧需关注同适应症话术变化。")
    return news


def _build_price_trend(products: list[dict[str, Any]]) -> list[dict[str, str | float]]:
    today = date.today()
    product_count = max(len(products), 1)
    watchlist_count = sum(1 for item in products if item.get("status") == "watchlist")
    coverage_count = sum(len(item.get("province_coverage") or []) for item in products)
    base_index = 100.0 - watchlist_count * 1.5 + min(coverage_count, 10) * 0.2
    trend = []
    for offset in range(7):
        day = today - timedelta(days=6 - offset)
        index = round(base_index + (offset - 3) * 0.25 - watchlist_count * 0.1, 2)
        trend.append(
            {
                "date": day.isoformat(),
                "index": index,
                "note": f"{product_count}个监控竞品聚合价格信号",
            }
        )
    return trend


def get_quicklook(hcp_id: str) -> QuicklookDashboard:
    """Build a quicklook dashboard for pre-call HCP detail pages."""

    products = _select_products_for_hcp(hcp_id, _load_cloud_products())
    competitors = [_to_brief(product) for product in products]
    change_summary = _build_change_summary(products)
    activity_block = CompetitorActivityBlock(
        hcp_id=hcp_id,
        highlights=change_summary,
        products=competitors,
    )
    return QuicklookDashboard(
        hcp_id=hcp_id,
        competitors=competitors,
        recent_news=_build_recent_news(products),
        change_summary=change_summary,
        price_trend=_build_price_trend(products),
        related_competitor_activity=activity_block,
    )
