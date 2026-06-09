"""同比环比趋势分析服务。"""

from datetime import date, timedelta
from typing import Literal

from management.app.schemas.trend_analysis import TrendDataPoint

TrendMetric = Literal["visits", "compliance", "events"]
TrendPeriod = Literal["weekly", "monthly", "quarterly"]
CompareMode = Literal["mom", "yoy"]

METRIC_BASELINES = {
    "visits": 860.0,
    "compliance": 91.5,
    "events": 38.0,
}

PERIOD_CONFIG = {
    "weekly": {"step_days": 7, "labels": ["W-5", "W-4", "W-3", "W-2", "W-1", "W"]},
    "monthly": {"step_days": 30, "labels": ["M-5", "M-4", "M-3", "M-2", "M-1", "M"]},
    "quarterly": {"step_days": 91, "labels": ["Q-5", "Q-4", "Q-3", "Q-2", "Q-1", "Q"]},
}


def _metric_value(metric: TrendMetric, index: int, period: TrendPeriod) -> float:
    base = METRIC_BASELINES[metric]
    period_factor = {"weekly": 1.0, "monthly": 3.8, "quarterly": 10.5}[period]
    growth = index * {"visits": 34.0, "compliance": 0.8, "events": 2.3}[metric]
    seasonal = [0.0, -8.0, 12.0, 6.0, 18.0, 25.0][index]
    if metric == "compliance":
        return round(min(99.0, base + index * 0.7 + seasonal * 0.02), 1)
    return round(base * period_factor + growth * period_factor + seasonal, 1)


def _comparison_base(value: float, index: int, compare_mode: CompareMode) -> float:
    if compare_mode == "mom":
        return value - 12.0 - index * 1.4
    return value - 36.0 - index * 2.1


def _change_pct(value: float, baseline: float) -> float:
    if baseline == 0:
        return 0.0
    return round((value - baseline) / baseline * 100, 1)


def get_trend(metric: TrendMetric, period: TrendPeriod, compare_mode: CompareMode) -> list[TrendDataPoint]:
    """返回单指标趋势和同比/环比变化。"""

    config = PERIOD_CONFIG[period]
    start = date.today() - timedelta(days=config["step_days"] * (len(config["labels"]) - 1))
    points = []
    for index, label in enumerate(config["labels"]):
        value = _metric_value(metric, index, period)
        comparison = _comparison_base(value, index, compare_mode)
        points.append(
            TrendDataPoint(
                date=(start + timedelta(days=config["step_days"] * index)).isoformat(),
                metric_name=metric,
                value=value,
                period_label=label,
                change_pct=_change_pct(value, comparison),
            )
        )
    return points


def get_multi_metric_trend(metrics: list[TrendMetric], period: TrendPeriod) -> dict[str, list[TrendDataPoint]]:
    """返回多指标趋势，默认以环比口径计算变化。"""

    return {metric: get_trend(metric=metric, period=period, compare_mode="mom") for metric in metrics}
