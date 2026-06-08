import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from opportunity.app.trend_router import (
    TrendPredictRequest,
    list_trends,
    trend_history,
    trend_predict,
    trends_by_topic,
)


def test_list_trends_returns_empty_success_payload():
    response = list_trends()

    assert response.status_code == 200
    payload = json.loads(response.body)
    assert payload["data"] == []


def test_trends_by_topic_delegates_to_service():
    service = MagicMock()
    service.get_trends_by_topic.return_value = {
        "topic": "oncology",
        "period": "monthly",
        "data_points": [{"period": "2026-01", "count": 4}],
        "total": 4,
    }

    response = trends_by_topic(
        topic="oncology",
        period="monthly",
        service=service,
        current_user={"sub": "2"},
    )

    service.get_trends_by_topic.assert_called_once_with("oncology", "monthly")
    assert response.data.topic == "oncology"
    assert response.data.total == 4
    assert response.data.data_points[0].count == 4


def test_trend_predict_passes_auth_header_and_user_id():
    service = MagicMock()
    service.predict_trend.return_value = {
        "topic": "diabetes",
        "prediction": "up",
        "confidence": "high",
        "driving_factors": ["publications"],
        "similar_topics": ["metabolism"],
        "data_points_months": 6,
    }
    request = SimpleNamespace(headers={"Authorization": "Bearer token"})
    body = TrendPredictRequest(topic="diabetes", context="new guideline")

    response = trend_predict(
        body=body,
        request=request,
        service=service,
        current_user={"sub": "5"},
    )

    service.predict_trend.assert_called_once_with(body, "Bearer token", 5)
    assert response.data.prediction == "up"
    assert response.data.driving_factors == ["publications"]


def test_trend_history_wraps_paginated_rows():
    service = MagicMock()
    service.list_history.return_value = (
        1,
        1,
        [
            {
                "id": 1,
                "topic": "oncology",
                "analysis_type": "prediction",
                "confidence": "medium",
            }
        ],
    )

    response = trend_history(page=1, page_size=5, service=service, current_user={"sub": "1"})

    service.list_history.assert_called_once_with(1, 5)
    assert response.data.total == 1
    assert response.data.items[0].topic == "oncology"
