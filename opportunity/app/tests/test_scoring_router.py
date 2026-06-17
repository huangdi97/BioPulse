import json
from unittest.mock import MagicMock

from opportunity.app.routers.scoring_router import ScoreUpdate, leaderboard, recalculate, set_heat_score


def test_leaderboard_wraps_paginated_service_result():
    service = MagicMock()
    service.leaderboard.return_value = (
        1,
        1,
        [
            {
                "id": 10,
                "name": "Launch",
                "heat_score": 88,
                "is_active": 1,
            }
        ],
    )

    response = leaderboard(
        page=2,
        page_size=10,
        stage="proposal",
        min_score=50,
        max_score=90,
        service=service,
        current_user={"sub": "1"},
    )

    service.leaderboard.assert_called_once_with(
        page=2,
        page_size=10,
        stage="proposal",
        min_score=50,
        max_score=90,
    )
    assert response.data.total == 1
    assert response.data.page == 2
    assert response.data.items[0].id == 10
    assert response.data.items[0].heat_score == 88


def test_set_heat_score_returns_json_response():
    service = MagicMock()
    service.set_heat_score.return_value = {"id": 2, "name": "Opp", "heat_score": 77}

    response = set_heat_score(
        opportunity_id=2,
        body=ScoreUpdate(heat_score=77),
        service=service,
        current_user={"sub": "1"},
    )

    assert response.status_code == 200
    payload = json.loads(response.body)
    assert payload["data"]["id"] == 2
    assert payload["data"]["heat_score"] == 77
    service.set_heat_score.assert_called_once_with(2, 77)


def test_recalculate_maps_result_model():
    service = MagicMock()
    service.recalculate.return_value = {
        "total_updated": 3,
        "average_score": 61.3,
        "top_score": 95,
        "bottom_score": 20,
    }

    response = recalculate(service=service, current_user={"sub": "1"})

    assert response.data.total_updated == 3
    assert response.data.top_score == 95
    service.recalculate.assert_called_once_with()
