"""竞品情报嵌入面板 API。"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Query

from pharma_intel.app.services.competitor_landscape_service import get_radar_chart_data
from pharma_intel.app.services.target_pipeline_service import get_target_pipeline_tree

router = APIRouter(prefix="/api/panel", tags=["竞品情报面板"])


def _sentiment_series(product_id: str, days: int = 30) -> dict:
    today = date.today()
    line = []
    positive_total = 0
    neutral_total = 0
    negative_total = 0
    seed = sum(ord(char) for char in product_id) % 7
    for offset in range(days):
        day = today - timedelta(days=days - offset - 1)
        positive = 16 + (offset + seed) % 8
        neutral = 22 + (offset * 2 + seed) % 6
        negative = 5 + (offset * 3 + seed) % 5
        positive_total += positive
        neutral_total += neutral
        negative_total += negative
        line.append(
            {
                "date": day.isoformat(),
                "positive": positive,
                "neutral": neutral,
                "negative": negative,
                "score": round((positive - negative) / (positive + neutral + negative), 3),
            }
        )
    return {
        "product_id": product_id,
        "line": line,
        "pie": [
            {"name": "positive", "value": positive_total},
            {"name": "neutral", "value": neutral_total},
            {"name": "negative", "value": negative_total},
        ],
    }


@router.get("/target-landscape", tags=["竞品情报面板"])
def target_landscape():
    tree = get_target_pipeline_tree()
    return {
        "chart_type": "target_pipeline_tree",
        "targets": tree.targets,
    }


@router.get("/competitor-landscape", tags=["竞品情报面板"])
def competitor_landscape(target_id: str = Query("tgt-pd1", description="靶点ID")):
    radar = get_radar_chart_data(target_id)
    return {
        "chart_type": "radar",
        "target_id": radar.target_id,
        "dimensions": radar.dimensions,
        "series": radar.series,
    }


@router.get("/sentiment-trend", tags=["竞品情报面板"])
def sentiment_trend(product_id: str = Query(..., description="产品ID")):
    return {
        "chart_type": "sentiment_line_and_pie",
        "data": _sentiment_series(product_id),
    }
