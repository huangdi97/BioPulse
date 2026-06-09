"""同比环比趋势分析 API。"""

from fastapi import APIRouter, Query

from management.app.services.trend_analysis_service import (
    CompareMode,
    TrendMetric,
    TrendPeriod,
    get_multi_metric_trend,
    get_trend,
)
from shared.base import success

router = APIRouter(prefix="/api/trend", tags=["趋势分析"])


@router.get("", summary="单指标趋势", description="获取拜访、合规或事件指标趋势，支持同比/环比", tags=["趋势分析"])
def metric_trend(
    metric: TrendMetric = Query("visits", description="指标: visits/compliance/events"),
    period: TrendPeriod = Query("monthly", description="统计周期: weekly/monthly/quarterly"),
    compare_mode: CompareMode = Query("mom", description="比较方式: mom/yoy"),
):
    data = get_trend(metric=metric, period=period, compare_mode=compare_mode)
    return success(data=data)


@router.get("/multi", summary="多指标趋势", description="获取多个指标的趋势数据", tags=["趋势分析"])
def multi_metric_trend(
    metrics: str = Query("visits,compliance", description="逗号分隔指标: visits,compliance,events"),
    period: TrendPeriod = Query("weekly", description="统计周期: weekly/monthly/quarterly"),
):
    metric_values = [item.strip() for item in metrics.split(",") if item.strip()]
    allowed = {"visits", "compliance", "events"}
    invalid = sorted(set(metric_values) - allowed)
    if invalid:
        from fastapi import HTTPException
        from starlette import status

        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Unsupported metrics: {', '.join(invalid)}")
    data = get_multi_metric_trend(metrics=metric_values, period=period)
    return success(data=data)
