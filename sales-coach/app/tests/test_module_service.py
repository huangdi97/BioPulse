from unittest.mock import MagicMock

from sales_coach.app.module_router import ModuleCreate, ModuleUpdate
from sales_coach.app.services.module_service import ModuleService


def test_create_module_passes_model_dump_and_audit_data(monkeypatch):
    repo = MagicMock()
    repo.create.return_value = 51
    monkeypatch.setattr(
        "sales_coach.app.services.module_service.ModuleRepository",
        MagicMock(return_value=repo),
    )

    service = ModuleService()
    service.db = object()
    result = service.create(
        ModuleCreate(
            title="Negotiation Basics",
            description="intro",
            category="soft_skills",
            difficulty="beginner",
        ),
        user_id=10,
    )

    assert result == {"id": 51}
    created = repo.create.call_args.args[0]
    assert created["title"] == "Negotiation Basics"
    assert created["difficulty"] == "beginner"
    assert repo.create.call_args.kwargs["extra"]["created_by"] == 10


def test_list_modules_builds_filter_arguments(monkeypatch):
    repo = MagicMock()
    repo.paginate_active.return_value = (1, 1, [{"id": 1, "title": "Module"}])
    monkeypatch.setattr(
        "sales_coach.app.services.module_service.ModuleRepository",
        MagicMock(return_value=repo),
    )

    service = ModuleService()
    service.db = object()
    result = service.list(page=4, page_size=12, category="clinical", difficulty="advanced")

    assert result == (1, 1, [{"id": 1, "title": "Module"}])
    repo.paginate_active.assert_called_once_with(
        page=4,
        page_size=12,
        conditions=["category = ?", "difficulty = ?"],
        params=["clinical", "advanced"],
        order_by="id DESC",
    )


def test_update_module_adds_updated_at_for_changes(monkeypatch):
    repo = MagicMock()
    repo.get_by_id.return_value = {
        "id": 2,
        "title": "Updated",
        "difficulty": "advanced",
        "is_active": 1,
    }
    monkeypatch.setattr(
        "sales_coach.app.services.module_service.ModuleRepository",
        MagicMock(return_value=repo),
    )

    service = ModuleService()
    service.db = object()
    result = service.update(2, ModuleUpdate(title="Updated", difficulty="advanced"))

    assert result["title"] == "Updated"
    update_payload = repo.update.call_args.args[1]
    assert update_payload["title"] == "Updated"
    assert update_payload["difficulty"] == "advanced"
    assert "updated_at" in update_payload


def test_delete_module_soft_deletes_after_existence_check(monkeypatch):
    repo = MagicMock()
    monkeypatch.setattr(
        "sales_coach.app.services.module_service.ModuleRepository",
        MagicMock(return_value=repo),
    )

    service = ModuleService()
    service.db = object()
    service.delete(9)

    repo.get_active_or_404.assert_called_once_with(9)
    repo.soft_delete.assert_called_once_with(9)
