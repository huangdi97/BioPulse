"""Utility functions for crawler data analysis — date parsing, data loading, and math helpers."""

from __future__ import annotations

import logging
import math
import sqlite3
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


def parse_date(value: Any) -> date | None:
    """Parse crawler date values without enforcing one input format."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def pct_change(old: float, new: float) -> float:
    """Return percentage change from old to new, or 0.0 if old is zero."""
    if old == 0:
        return 0.0
    return round((new - old) / old * 100, 2)


def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert value to float, returning default on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def linear_regression_slope(values: list[float]) -> float:
    """Return the least-squares slope for y values over evenly spaced x values."""
    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(values) / n
    denom = sum((x - x_mean) ** 2 for x in xs)
    if denom == 0:
        return 0.0
    return sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, values)) / denom


def moving_average(values: list[float], window: int = 7) -> list[float]:
    """Compute trailing moving average with the given window size."""
    if not values:
        return []
    window = max(1, min(window, len(values)))
    result = []
    for idx in range(len(values)):
        start = max(0, idx - window + 1)
        chunk = values[start : idx + 1]
        result.append(round(sum(chunk) / len(chunk), 2))
    return result


def load_price_records(product_id: int | str, days: int | None = None, storage: Any | None = None) -> list[dict[str, Any]]:
    """Load price records from crawler storage, falling back to deterministic samples."""
    records: list[dict[str, Any]] = []
    _name = "load_price_records"
    try:
        from cloud.app.crawler.models import PriceRecord
        from cloud.app.crawler.storage import get_storage

        active_storage = storage or get_storage()
        records = active_storage.query_records(PriceRecord, {"product_id": int(product_id)})
    except ImportError:
        records = []
    except (sqlite3.Error, OSError) as e:
        logger.warning("DB error in %s: %s", _name, e)
        records = []

    if not records:
        records = sample_price_records(int(product_id), days or 30)

    cutoff = date.today() - timedelta(days=days - 1) if days else None
    normalized = []
    for record in records:
        record_date = parse_date(record.get("date") or record.get("timestamp"))
        if cutoff and record_date and record_date < cutoff:
            continue
        normalized.append(
            {
                "product_id": int(record.get("product_id", product_id)),
                "price": safe_float(record.get("price")),
                "province": record.get("province") or "全国",
                "date": (record_date or date.today()).isoformat(),
                "source": record.get("source") or "crawler",
            }
        )
    return sorted(normalized, key=lambda item: (item["date"], item["province"]))


def daily_average(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group records by date and compute daily average price."""
    grouped: dict[str, list[float]] = defaultdict(list)
    for record in records:
        grouped[record["date"]].append(safe_float(record.get("price")))
    return [{"date": day, "price": round(sum(values) / len(values), 2)} for day, values in sorted(grouped.items()) if values]


def latest_by(records: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    """Return the latest record keyed by the given field value."""
    latest: dict[str, dict[str, Any]] = {}
    for record in sorted(records, key=lambda item: item["date"]):
        latest[str(record.get(field) or "")] = record
    return latest


def sample_price_records(product_id: int, days: int = 30) -> list[dict[str, Any]]:
    """Create stable sample data when crawler storage has not collected prices yet."""
    provinces = ["北京", "上海", "广东", "四川"]
    base = 100 + (sum(ord(char) for char in str(product_id)) % 35)
    start = date.today() - timedelta(days=max(days, 1) - 1)
    records = []
    for offset in range(max(days, 1)):
        current = start + timedelta(days=offset)
        trend = offset * (0.18 if product_id % 2 else -0.12)
        wave = math.sin(offset / 3.0) * 1.8
        for p_idx, province in enumerate(provinces):
            province_delta = p_idx * 1.7
            price = round(base + trend + wave + province_delta, 2)
            records.append(
                {
                    "product_id": product_id,
                    "price": price,
                    "province": province,
                    "date": current.isoformat(),
                    "source": "sample",
                }
            )
    return records


def sample_public_opinions(keyword: str, days: int = 7, platforms: list[str] | None = None) -> list[dict[str, Any]]:
    """Generate sample public opinion data when no real data is available."""
    platforms = platforms or ["微博", "小红书", "新闻", "招标公告"]
    templates = [
        ("疗效数据表现积极，医生反馈较好", "positive"),
        ("价格调整引发渠道观望", "neutral"),
        ("部分用户反馈供应不稳定", "negative"),
        ("新推广活动覆盖重点医院", "positive"),
    ]
    start = date.today() - timedelta(days=max(days, 1) - 1)
    records = []
    for offset in range(max(days, 1)):
        current = start + timedelta(days=offset)
        for p_idx, platform in enumerate(platforms):
            repeats = 1 + ((offset + p_idx + len(keyword)) % 3)
            for ridx in range(repeats):
                text, sentiment = templates[(offset + p_idx + ridx) % len(templates)]
                records.append(
                    {
                        "platform": platform,
                        "title": f"{keyword}{platform}动态",
                        "content": f"{keyword}{text}",
                        "sentiment": sentiment,
                        "publish_date": current.isoformat(),
                        "url": "",
                    }
                )
    return records


def load_public_opinions(
    keyword: str,
    days: int | None = None,
    platforms: list[str] | None = None,
    storage: Any | None = None,
) -> list[dict[str, Any]]:
    """Load public opinions from storage, filtered by keyword, falling back to samples."""
    records: list[dict[str, Any]] = []
    _name = "load_public_opinions"
    try:
        from cloud.app.crawler.models import PublicOpinion
        from cloud.app.crawler.storage import get_storage

        active_storage = storage or get_storage()
        query_filters = {"platform": platforms} if platforms else None
        records = active_storage.query_records(PublicOpinion, query_filters)
    except ImportError:
        records = []
    except (sqlite3.Error, OSError) as e:
        logger.warning("DB error in %s: %s", _name, e)
        records = []

    keyword_lower = keyword.lower()
    cutoff = date.today() - timedelta(days=days - 1) if days else None
    normalized = []
    for record in records:
        publish_date = parse_date(record.get("publish_date") or record.get("created_at"))
        haystack = f"{record.get('title', '')} {record.get('content', '')}".lower()
        if keyword_lower and keyword_lower not in haystack:
            continue
        if cutoff and publish_date and publish_date < cutoff:
            continue
        platform = record.get("platform") or "未知平台"
        if platforms and platform not in platforms:
            continue
        normalized.append(
            {
                "platform": platform,
                "title": record.get("title") or "",
                "content": record.get("content") or "",
                "sentiment": record.get("sentiment") or "neutral",
                "publish_date": (publish_date or date.today()).isoformat(),
                "url": record.get("url") or "",
            }
        )

    if normalized:
        return sorted(normalized, key=lambda item: (item["publish_date"], item["platform"]))
    return sample_public_opinions(keyword, days or 7, platforms)


__all__ = [
    "daily_average",
    "latest_by",
    "linear_regression_slope",
    "load_price_records",
    "load_public_opinions",
    "moving_average",
    "parse_date",
    "pct_change",
    "safe_float",
    "sample_price_records",
    "sample_public_opinions",
]
