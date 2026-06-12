"""价格变动预警服务。"""

from __future__ import annotations

from datetime import datetime, timezone

from ..schemas.price_alert import AlertConfig, PriceAlert
from .price_monitor_service import get_price_points_for_alert

_DEFAULT_CONFIG = AlertConfig(
    user_id="user-default",
    product_ids=["prod-001", "prod-002"],
    threshold_pct=5.0,
    notify_channels=["in_app", "email"],
)

_CONFIGS: dict[str, AlertConfig] = {_DEFAULT_CONFIG.user_id: _DEFAULT_CONFIG}
_ALERT_HISTORY: list[dict] = [
    {
        "product_id": "prod-001",
        "old_price": 108.4,
        "new_price": 101.8,
        "change_pct": -6.09,
        "threshold": 5.0,
        "trigger_time": "2026-05-15T09:30:00+00:00",
        "severity": "medium",
        "reason": "price_drop_exceeded_threshold",
        "notified_channels": ["in_app", "email"],
    }
]


async def check_price_threshold(product_id: str, new_price: float) -> dict:
    """检查价格是否跌破历史 5% 分位或超过配置阈值。

    Args:
        product_id: 产品ID
        new_price: 最新价格

    Returns:
        包含价格变动详情、触发状态和通知渠道的字典
    """
    prices = get_price_points_for_alert(product_id)
    old_price = prices[-1]
    fifth_percentile = _percentile(prices, 5)
    config = _find_config_for_product(product_id)
    change_pct = round((new_price - old_price) / old_price * 100, 2)
    threshold = config.threshold_pct

    breached_percentile = new_price <= fifth_percentile
    breached_threshold = change_pct <= -threshold
    severity = _severity(change_pct, threshold, breached_percentile)

    result = {
        "product_id": product_id,
        "old_price": old_price,
        "new_price": new_price,
        "change_pct": change_pct,
        "threshold": threshold,
        "fifth_percentile_price": round(fifth_percentile, 2),
        "triggered": breached_percentile or breached_threshold,
        "severity": severity,
        "reason": _reason(breached_percentile, breached_threshold),
        "notified_channels": config.notify_channels if breached_percentile or breached_threshold else [],
        "trigger_time": datetime.now(timezone.utc).isoformat(),
    }

    if result["triggered"]:
        alert = PriceAlert(
            product_id=product_id,
            old_price=old_price,
            new_price=new_price,
            change_pct=change_pct,
            threshold=threshold,
            trigger_time=datetime.now(timezone.utc),
            severity=severity,
        ).dict()
        alert.update(
            {
                "reason": result["reason"],
                "notified_channels": result["notified_channels"],
            }
        )
        alert["trigger_time"] = alert["trigger_time"].isoformat()
        _ALERT_HISTORY.insert(0, alert)

    return result


async def configure_alert(config: AlertConfig) -> dict:
    """创建或更新价格预警配置。

    Args:
        config: 预警配置对象（包含用户ID、产品列表、阈值和通知渠道）

    Returns:
        更新后的配置信息字典
    """
    _CONFIGS[config.user_id] = config
    return {
        "user_id": config.user_id,
        "product_ids": config.product_ids,
        "threshold_pct": config.threshold_pct,
        "notify_channels": config.notify_channels,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


async def get_alert_history() -> dict:
    """获取价格预警历史记录。

    Returns:
        包含预警总数和预警列表的字典
    """
    return {
        "total": len(_ALERT_HISTORY),
        "alerts": _ALERT_HISTORY,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


def _find_config_for_product(product_id: str) -> AlertConfig:
    """查找包含指定产品的预警配置。

    Args:
        product_id: 产品ID

    Returns:
        匹配的预警配置对象，未找到则返回默认配置
    """
    for config in _CONFIGS.values():
        if product_id in config.product_ids:
            return config
    return _DEFAULT_CONFIG


def _percentile(values: list[float], percentile: float) -> float:
    """计算百分位数值（线性插值法）。

    Args:
        values: 数值列表
        percentile: 百分位数（0-100）

    Returns:
        对应百分位的计算值
    """
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * percentile / 100
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _severity(change_pct: float, threshold: float, breached_percentile: bool) -> str:
    """根据价格变动幅度和分位阈值判断严重级别。

    Args:
        change_pct: 价格变动百分比
        threshold: 配置阈值
        breached_percentile: 是否跌破历史分位

    Returns:
        严重级别（high/medium/normal）
    """
    if breached_percentile or change_pct <= -(threshold * 2):
        return "high"
    if change_pct <= -threshold:
        return "medium"
    return "normal"


def _reason(breached_percentile: bool, breached_threshold: bool) -> str:
    """生成预警触发原因描述。

    Args:
        breached_percentile: 是否跌破历史分位
        breached_threshold: 是否超过配置阈值

    Returns:
        触发原因字符串
    """
    if breached_percentile:
        return "below_historical_5th_percentile"
    if breached_threshold:
        return "price_drop_exceeded_threshold"
    return "within_threshold"
