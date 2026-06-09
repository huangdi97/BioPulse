"""招标价格监控服务。"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.encoders import jsonable_encoder

from ..database import get_cache, set_cache
from ..schemas.price_monitor import CentralizedProcurement, PriceHistory, ProvincePrice

_PROVINCE_LABELS = {
    "jiangsu": "江苏",
    "zhejiang": "浙江",
    "guangdong": "广东",
    "shanghai": "上海",
    "beijing": "北京",
    "sichuan": "四川",
    "hubei": "湖北",
    "shandong": "山东",
}

_MANUFACTURERS = [
    "恒瑞医药",
    "齐鲁制药",
    "正大天晴",
    "复星医药",
    "石药集团",
    "信达生物",
]

_PRICE_SERIES = {
    "prod-001": [
        {"date": "2025-10-15", "price": 128.5, "source": "省级挂网"},
        {"date": "2025-11-15", "price": 123.8, "source": "联盟采购"},
        {"date": "2025-12-15", "price": 121.2, "source": "省级挂网"},
        {"date": "2026-01-15", "price": 116.9, "source": "集采续约"},
        {"date": "2026-02-15", "price": 112.6, "source": "省级挂网"},
        {"date": "2026-03-15", "price": 108.4, "source": "联盟采购"},
        {"date": "2026-04-15", "price": 105.2, "source": "省级挂网"},
        {"date": "2026-05-15", "price": 101.8, "source": "集采续约"},
    ],
    "prod-002": [
        {"date": "2025-10-15", "price": 86.4, "source": "省级挂网"},
        {"date": "2025-11-15", "price": 85.1, "source": "省级挂网"},
        {"date": "2025-12-15", "price": 82.7, "source": "联盟采购"},
        {"date": "2026-01-15", "price": 80.6, "source": "省级挂网"},
        {"date": "2026-02-15", "price": 77.9, "source": "集采续约"},
        {"date": "2026-03-15", "price": 76.5, "source": "省级挂网"},
        {"date": "2026-04-15", "price": 74.8, "source": "联盟采购"},
        {"date": "2026-05-15", "price": 73.2, "source": "省级挂网"},
    ],
}


async def get_province_price(product_id: str, province: str) -> dict:
    """获取指定产品在指定省份的最新中标价格。"""
    province_key = province.lower()
    cache_key = f"price:province:{product_id}:{province_key}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    result = jsonable_encoder(_build_province_price(product_id, province_key))
    result["last_updated"] = datetime.now(timezone.utc).isoformat()
    set_cache(cache_key, result, ttl=300)
    return result


async def get_price_history(product_id: str) -> dict:
    """获取产品历史价格序列及波动率。"""
    cache_key = f"price:history:{product_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    price_series = _get_price_series(product_id)
    prices = [point["price"] for point in price_series]
    avg_price = sum(prices) / len(prices)
    volatility = round((max(prices) - min(prices)) / avg_price, 4)

    result = jsonable_encoder(
        PriceHistory(
            product_id=product_id,
            province="全国",
            price_series=price_series,
            volatility=volatility,
        )
    )
    result["last_updated"] = datetime.now(timezone.utc).isoformat()
    set_cache(cache_key, result, ttl=300)
    return result


async def get_centralized_comparison(product_id: str, round: int) -> dict:
    """获取产品在指定集采批次的中选对比信息。"""
    cache_key = f"price:centralized:{product_id}:{round}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    series = _get_price_series(product_id)
    first_price = series[0]["price"]
    latest_price = series[-1]["price"]
    reduction_rate = round_number((first_price - latest_price) / first_price * 100)

    procurement = CentralizedProcurement(
        round=round,
        products=[product_id, "prod-002", "prod-003"],
        winning_companies=_select_companies(product_id, round),
        price_reduction_rate=reduction_rate,
    )
    result = jsonable_encoder(procurement)
    result.update(
        {
            "product_id": product_id,
            "pre_procurement_price": first_price,
            "latest_winning_price": latest_price,
            "comparison": "below_market_average" if reduction_rate >= 15 else "stable",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
    )
    set_cache(cache_key, result, ttl=300)
    return result


def get_price_points_for_alert(product_id: str) -> list[float]:
    """返回价格预警计算使用的历史价格。"""
    return [point["price"] for point in _get_price_series(product_id)]


def _build_province_price(product_id: str, province_key: str) -> ProvincePrice:
    province_label = _PROVINCE_LABELS.get(province_key, province_key)
    series = _get_price_series(product_id)
    base_price = series[-1]["price"]
    adjustment = (_stable_score(province_key) % 13 - 6) * 0.9
    product_adjustment = (_stable_score(product_id) % 7) * 0.35

    return ProvincePrice(
        product_id=product_id,
        province=province_label,
        winning_price=round_number(base_price + adjustment + product_adjustment),
        bid_date=series[-1]["date"],
        procurement_volume=18000 + (_stable_score(product_id + province_key) % 42000),
        manufacturer=_MANUFACTURERS[_stable_score(product_id) % len(_MANUFACTURERS)],
    )


def _get_price_series(product_id: str) -> list[dict]:
    if product_id in _PRICE_SERIES:
        return [point.copy() for point in _PRICE_SERIES[product_id]]

    base = 96 + (_stable_score(product_id) % 40)
    dates = [
        "2025-10-15",
        "2025-11-15",
        "2025-12-15",
        "2026-01-15",
        "2026-02-15",
        "2026-03-15",
        "2026-04-15",
        "2026-05-15",
    ]
    return [
        {
            "date": item_date,
            "price": round_number(base - index * 2.7 + (index % 3) * 0.8),
            "source": "省级挂网" if index % 2 == 0 else "联盟采购",
        }
        for index, item_date in enumerate(dates)
    ]


def _select_companies(product_id: str, round: int) -> list[str]:
    start = (_stable_score(product_id) + round) % len(_MANUFACTURERS)
    return [_MANUFACTURERS[(start + index) % len(_MANUFACTURERS)] for index in range(3)]


def _stable_score(value: str) -> int:
    return sum((index + 1) * ord(char) for index, char in enumerate(value))


def round_number(value: float) -> float:
    return round(value, 2)
