"""情报收集来源（竞品与市场）。"""

from __future__ import annotations

import sqlite3
from typing import Any


def query_competitor_intel(db: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    """查询竞品动态简报。

    Args:
        db: 数据库连接。
        args: 包含窗口与拜访上下文的参数。

    Returns:
        竞品动态结构化摘要。
    """
    try:
        from ..services.competitor_brief_service import CompetitorBriefService

        brief = CompetitorBriefService(db=db).generate_weekly_brief()
    except Exception as exc:
        brief = fallback_competitor_brief(exc)
    return {
        "hcp_id": args.get("hcp_id"),
        "window_days": args.get("window_days", 7),
        "summary": brief.get("summary", {}),
        "sections": brief.get("sections", {}),
        "recommendations": brief.get("recommendations", []),
        "sources": brief.get("sources", []),
    }


def fallback_competitor_brief(exc: Exception) -> dict[str, Any]:
    """生成竞品情报降级简报。

    Args:
        exc: 原始服务异常。

    Returns:
        可用于策略推荐的竞品情报结构。
    """
    return {
        "summary": {
            "new_product_launches": 1,
            "price_adjustments": 0,
            "marketing_activities": 1,
            "negative_events": 0,
            "tracked_products": 0,
        },
        "sections": {
            "new_product_launches": [
                {
                    "title": "竞品动态待确认",
                    "summary": "竞品情报服务暂不可用，建议拜访前复核最新批准与活动信息。",
                    "impact_level": "medium",
                }
            ],
            "marketing_activities": [],
            "negative_events": [],
        },
        "recommendations": ["复核近期竞品公开信息，并准备合规差异化话术。"],
        "sources": [f"fallback:{exc.__class__.__name__}"],
    }


def query_market_intel(db: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    """查询市场情报。

    Args:
        db: 数据库连接。
        args: 包含关键词与数量上限的参数。

    Returns:
        市场情报列表与摘要。
    """
    keywords = args.get("keywords") or []
    limit = int(args.get("limit", 10))
    items = safe_market_items(db, keywords, limit)
    return {
        "keywords": keywords,
        "items": items,
        "item_count": len(items),
        "high_impact_count": sum(1 for item in items if item.get("impact_level") == "high"),
    }


def safe_market_items(db: sqlite3.Connection, keywords: list[str], limit: int) -> list[dict[str, Any]]:
    """安全读取市场情报。

    Args:
        db: 数据库连接。
        keywords: 查询关键词列表。
        limit: 最大返回条数。

    Returns:
        市场情报字典列表。
    """
    if not db:
        return []
    try:
        from ..services import MarketIntelService

        service = MarketIntelService(db)
        keyword = str(keywords[0]) if keywords else None
        page = service.list_items(keyword=keyword, page=1, page_size=limit)
        return list(page.items)
    except Exception:
        logger.warning("Intel collector异常", exc_info=True)
        return []
