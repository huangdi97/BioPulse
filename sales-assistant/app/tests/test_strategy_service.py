import json
from unittest.mock import MagicMock

from sales_assistant.app.services.strategy_service import StrategyService
from sales_assistant.app.strategy_router import (
    StrategyGenerateRequest,
    StrategySimulateRequest,
)


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def test_generate_strategy_parses_ai_reply_and_saves(monkeypatch):
    repo = MagicMock()
    repo.create.return_value = 21
    repo.get_by_id.return_value = {
        "id": 21,
        "hcp_name": "Dr. Sun",
        "goal": "increase adoption",
        "approach": "evidence first",
        "talking_points": "trial data",
        "expected_outcome": "follow-up",
        "is_active": 1,
    }
    monkeypatch.setattr(
        "sales_assistant.app.services.strategy_service.StrategyRepository",
        MagicMock(return_value=repo),
    )
    monkeypatch.setattr(
        "sales_assistant.app.services.strategy_service.urllib.request.urlopen",
        MagicMock(
            return_value=_Response(
                {"data": {"reply": ('{"approach":"evidence first","talking_points":"trial data","expected_outcome":"follow-up"}')}}
            )
        ),
    )

    service = StrategyService(db=object())
    result = service.generate_strategy(
        StrategyGenerateRequest(
            hcp_name="Dr. Sun",
            goal="increase adoption",
            hcp_tier="A",
            product_name="DrugX",
        ),
        user_id=8,
    )

    assert result["id"] == 21
    created = repo.create.call_args.args[0]
    assert created["approach"] == "evidence first"
    assert created["talking_points"] == "trial data"
    assert repo.create.call_args.kwargs["extra"]["created_by"] == 8


def test_generate_strategy_uses_empty_fields_when_ai_fails(monkeypatch):
    repo = MagicMock()
    repo.create.return_value = 22
    repo.get_by_id.return_value = {"id": 22, "hcp_name": "Dr. Xu", "is_active": 1}
    monkeypatch.setattr(
        "sales_assistant.app.services.strategy_service.StrategyRepository",
        MagicMock(return_value=repo),
    )
    monkeypatch.setattr(
        "sales_assistant.app.services.strategy_service.urllib.request.urlopen",
        MagicMock(side_effect=OSError("gateway unavailable")),
    )

    service = StrategyService(db=object())
    service.generate_strategy(
        StrategyGenerateRequest(hcp_name="Dr. Xu", goal="retain account"),
        user_id=9,
    )

    created = repo.create.call_args.args[0]
    assert created["approach"] == ""
    assert created["talking_points"] == ""
    assert created["expected_outcome"] == ""


def test_simulate_strategy_uses_history_when_ai_fails(monkeypatch):
    row = {"cnt": 4, "avg_eff": 0.63}
    db = MagicMock()
    db.execute.return_value.fetchone.return_value = row
    monkeypatch.setattr(
        "sales_assistant.app.services.strategy_service.urllib.request.urlopen",
        MagicMock(side_effect=TimeoutError("timeout")),
    )

    service = StrategyService(db=db)
    result = service.simulate_strategy(
        StrategySimulateRequest(
            hcp_name="Dr. Gao",
            approach="evidence first",
            product_name="DrugY",
        )
    )

    assert result == {
        "predicted_effectiveness": 0.63,
        "confidence": "低",
        "similar_cases": 4,
    }
    db.execute.assert_called_once()
