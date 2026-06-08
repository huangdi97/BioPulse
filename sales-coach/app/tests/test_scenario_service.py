from unittest.mock import MagicMock

from sales_coach.app.scenario_router import ScenarioCreate, ScenarioUpdate
from sales_coach.app.services.scenario_service import ScenarioService


def test_create_scenario_uses_explicit_fields_and_audit_data(monkeypatch):
    repo = MagicMock()
    repo.create.return_value = 41
    monkeypatch.setattr(
        "sales_coach.app.services.scenario_service.ScenarioRepository",
        MagicMock(return_value=repo),
    )

    service = ScenarioService()
    service.db = object()
    result = service.create(
        ScenarioCreate(
            title="Objection Handling",
            role_setting="rep and HCP",
            goal="handle price concern",
            difficulty="hard",
            category="objection",
            content="dialogue",
            tips="ask questions",
        ),
        user_id=6,
    )

    assert result == {"id": 41}
    kwargs = repo.create.call_args.kwargs
    assert kwargs["data"]["title"] == "Objection Handling"
    assert kwargs["data"]["tips"] == "ask questions"
    assert kwargs["extra"]["created_by"] == 6
    assert "updated_at" in kwargs["extra"]


def test_list_scenarios_builds_active_filters(monkeypatch):
    repo = MagicMock()
    repo.paginate_active.return_value = (2, 1, [{"id": 1}, {"id": 2}])
    monkeypatch.setattr(
        "sales_coach.app.services.scenario_service.ScenarioRepository",
        MagicMock(return_value=repo),
    )

    service = ScenarioService()
    service.db = object()
    result = service.list(page=1, page_size=10, category="negotiation", difficulty="medium")

    assert result == (2, 1, [{"id": 1}, {"id": 2}])
    repo.paginate_active.assert_called_once_with(
        page=1,
        page_size=10,
        conditions=["category = ?", "difficulty = ?"],
        params=["negotiation", "medium"],
        order_by="id DESC",
    )


def test_update_scenario_returns_existing_row_when_no_updates(monkeypatch):
    repo = MagicMock()
    repo.get_by_id.return_value = {"id": 3, "title": "Scenario", "is_active": 1}
    monkeypatch.setattr(
        "sales_coach.app.services.scenario_service.ScenarioRepository",
        MagicMock(return_value=repo),
    )

    service = ScenarioService()
    service.db = object()
    result = service.update(3, ScenarioUpdate())

    assert result["title"] == "Scenario"
    repo.get_active_or_404.assert_called_once_with(3)
    repo.update.assert_not_called()


def test_delete_scenario_soft_deletes_after_existence_check(monkeypatch):
    repo = MagicMock()
    monkeypatch.setattr(
        "sales_coach.app.services.scenario_service.ScenarioRepository",
        MagicMock(return_value=repo),
    )

    service = ScenarioService()
    service.db = object()
    service.delete(8)

    repo.get_active_or_404.assert_called_once_with(8)
    repo.soft_delete.assert_called_once_with(8)
