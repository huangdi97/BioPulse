"""竞品情报 Agent 工具函数。

这些函数面向 MCP/Agent 调用，返回可直接序列化的结构化 JSON 数据。
"""

from __future__ import annotations

from datetime import date, timedelta
from statistics import mean
from typing import Iterable

PRODUCTS: dict[str, dict] = {
    "prod-001": {
        "id": "prod-001",
        "name": "瑞舒伐他汀钙片",
        "company": "Acme Pharma",
        "category": "cardiovascular",
        "indication": "hyperlipidemia",
        "province_coverage": ["jiangsu", "zhejiang", "shanghai"],
        "status": "active",
    },
    "prod-002": {
        "id": "prod-002",
        "name": "阿托伐他汀钙片",
        "company": "Northstar Bio",
        "category": "cardiovascular",
        "indication": "hyperlipidemia",
        "province_coverage": ["jiangsu", "guangdong", "beijing"],
        "status": "active",
    },
    "prod-003": {
        "id": "prod-003",
        "name": "依折麦布片",
        "company": "Zenith Therapeutics",
        "category": "cardiovascular",
        "indication": "hypercholesterolemia",
        "province_coverage": ["zhejiang", "shanghai", "sichuan"],
        "status": "watchlist",
    },
}

_BASE_PRICES = {
    ("prod-001", "jiangsu"): 38.6,
    ("prod-001", "zhejiang"): 39.2,
    ("prod-001", "shanghai"): 40.1,
    ("prod-002", "jiangsu"): 35.8,
    ("prod-002", "guangdong"): 36.5,
    ("prod-002", "beijing"): 37.3,
    ("prod-003", "zhejiang"): 46.8,
    ("prod-003", "shanghai"): 47.5,
    ("prod-003", "sichuan"): 45.9,
}


def _normalize_ids(product_ids: Iterable[str] | str) -> list[str]:
    if isinstance(product_ids, str):
        raw_ids = product_ids.split(",")
    else:
        raw_ids = list(product_ids)
    return [item.strip() for item in raw_ids if item and item.strip()]


def _price_points(product_id: str, province: str = "jiangsu", days: int = 30) -> list[dict]:
    base_price = _BASE_PRICES.get((product_id, province), 42.0)
    today = date.today()
    points = []
    for offset in range(max(days, 1)):
        day = today - timedelta(days=days - offset - 1)
        drift = (offset % 9 - 4) * 0.18
        campaign_drop = -2.2 if offset == max(days, 1) - 8 and days >= 14 else 0
        price = round(base_price + drift + campaign_drop, 2)
        points.append({"date": day.isoformat(), "price": price, "province": province})
    return points


def price_monitor(product_id: str, province: str) -> dict:
    """查询某产品某省价格。"""

    product = PRODUCTS.get(product_id)
    points = _price_points(product_id, province, days=30)
    latest = points[-1]["price"]
    previous = points[-8]["price"] if len(points) >= 8 else latest
    change_pct = round((latest - previous) / previous * 100, 2) if previous else 0
    return {
        "tool": "price_monitor",
        "product_id": product_id,
        "product_name": product["name"] if product else "unknown",
        "province": province,
        "currency": "CNY",
        "latest_price": latest,
        "weekly_change_pct": change_pct,
        "trend": points,
        "source": "mock_competitor_price_feed",
    }


def sentiment_analysis(keyword: str, days: int) -> dict:
    """查询关键词舆情趋势。"""

    days = max(1, min(days, 365))
    today = date.today()
    timeline = []
    positive_total = 0
    neutral_total = 0
    negative_total = 0
    for offset in range(days):
        day = today - timedelta(days=days - offset - 1)
        positive = 18 + offset % 7
        neutral = 24 + offset % 5
        negative = 6 + (offset * 2) % 6
        positive_total += positive
        neutral_total += neutral
        negative_total += negative
        total = positive + neutral + negative
        timeline.append(
            {
                "date": day.isoformat(),
                "positive": positive,
                "neutral": neutral,
                "negative": negative,
                "score": round((positive - negative) / total, 3),
            }
        )
    total_mentions = positive_total + neutral_total + negative_total
    return {
        "tool": "sentiment_analysis",
        "keyword": keyword,
        "days": days,
        "summary": {
            "mentions": total_mentions,
            "positive": positive_total,
            "neutral": neutral_total,
            "negative": negative_total,
            "sentiment_score": round((positive_total - negative_total) / total_mentions, 3),
        },
        "trend": timeline,
        "source": "mock_social_listening_feed",
    }


def competitive_comparison(product_ids: Iterable[str] | str) -> dict:
    """多产品对比。"""

    ids = _normalize_ids(product_ids)
    products = [PRODUCTS[item] for item in ids if item in PRODUCTS]
    rows = []
    for index, product in enumerate(products):
        province = product["province_coverage"][0]
        price = price_monitor(product["id"], province)
        price_index = max(60, min(100, round(100 - price["latest_price"])))
        rows.append(
            {
                "product_id": product["id"],
                "product_name": product["name"],
                "company": product["company"],
                "category": product["category"],
                "indication": product["indication"],
                "coverage_count": len(product["province_coverage"]),
                "price_index": price_index,
                "sentiment_index": 72 + index * 5,
                "access_index": 68 + len(product["province_coverage"]) * 4,
                "risk_level": "medium" if product["status"] == "watchlist" else "low",
            }
        )
    leaders = {
        "price": min(rows, key=lambda item: item["price_index"])["product_id"] if rows else None,
        "sentiment": max(rows, key=lambda item: item["sentiment_index"])["product_id"] if rows else None,
        "access": max(rows, key=lambda item: item["access_index"])["product_id"] if rows else None,
    }
    return {
        "tool": "competitive_comparison",
        "product_ids": ids,
        "dimensions": ["price_index", "sentiment_index", "access_index", "coverage_count"],
        "items": rows,
        "leaders": leaders,
    }


def strategy_suggestion(product_id: str, competitor_ids: Iterable[str] | str) -> dict:
    """AI生成策略建议。"""

    competitors = _normalize_ids(competitor_ids)
    comparison = competitive_comparison([product_id, *competitors])
    current = next((item for item in comparison["items"] if item["product_id"] == product_id), None)
    peer_scores = [item["sentiment_index"] for item in comparison["items"] if item["product_id"] != product_id]
    peer_sentiment_avg = round(mean(peer_scores), 2) if peer_scores else None
    suggestions = [
        {
            "priority": "high",
            "theme": "price_access",
            "action": "优先跟踪核心省份挂网价与集采续约节奏，识别短期价格下探窗口。",
            "expected_impact": "提升准入谈判和区域价格防守效率",
        },
        {
            "priority": "medium",
            "theme": "medical_value",
            "action": "围绕差异化适应症证据补强医学沟通材料，降低同质化竞品冲击。",
            "expected_impact": "提升专家端认知稳定性",
        },
        {
            "priority": "medium",
            "theme": "sentiment_response",
            "action": "对负面舆情峰值建立24小时内复盘与回应机制。",
            "expected_impact": "降低舆情扩散风险",
        },
    ]
    return {
        "tool": "strategy_suggestion",
        "product_id": product_id,
        "competitor_ids": competitors,
        "baseline": current,
        "peer_sentiment_avg": peer_sentiment_avg,
        "suggestions": suggestions,
        "generated_by": "competitor_intel_rule_engine",
    }
