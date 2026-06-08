import json
from unittest.mock import MagicMock

from sales_coach.app.assessment_router import AssessmentCreate, AssessmentUpdate
from sales_coach.app.services.assessment_service import AssessmentService


def test_calculate_auto_score_penalizes_short_user_entries():
    result = AssessmentService.calculate_auto_score(
        [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "请继续"},
            {"role": "user", "content": "我会介绍临床证据"},
        ]
    )

    scores = result["scores"]
    assert scores["compliance"] == 85
    assert scores["overall"] < 80
    assert json.loads(result["score_breakdown"]) == scores


def test_create_excludes_title_and_closes_connection(monkeypatch):
    repo = MagicMock()
    repo.create.return_value = 31
    repo_cls = MagicMock(return_value=repo)
    conn = MagicMock()
    service = AssessmentService()
    monkeypatch.setattr(service, "_connection", MagicMock(return_value=conn))
    monkeypatch.setattr("sales_coach.app.services.assessment_service.AssessmentRepository", repo_cls)

    result = service.create(
        AssessmentCreate(
            title="Quarterly Review",
            trainee_name="Li Ming",
            current_level="beginner",
        ),
        user_id=3,
    )

    assert result == {"id": 31}
    created = repo.create.call_args.args[0]
    assert "title" not in created
    assert created["trainee_name"] == "Li Ming"
    assert repo.create.call_args.kwargs["extra"]["created_by"] == 3
    conn.close.assert_called_once_with()


def test_list_builds_filters_and_closes_connection(monkeypatch):
    repo = MagicMock()
    repo.paginate_active.return_value = (1, 1, [{"id": 1}])
    conn = MagicMock()
    service = AssessmentService()
    monkeypatch.setattr(service, "_connection", MagicMock(return_value=conn))
    monkeypatch.setattr(
        "sales_coach.app.services.assessment_service.AssessmentRepository",
        MagicMock(return_value=repo),
    )

    result = service.list(
        page=2,
        page_size=5,
        trainee_name="Zhang",
        current_level="beginner",
        target_level="advanced",
    )

    assert result == (1, 1, [{"id": 1}])
    repo.paginate_active.assert_called_once_with(
        2,
        5,
        ["trainee_name LIKE ?", "current_level = ?", "target_level = ?"],
        ["%Zhang%", "beginner", "advanced"],
    )
    conn.close.assert_called_once_with()


def test_update_assessment_with_reflection_writes_notes(monkeypatch):
    repo = MagicMock()
    repo.get_by_id.return_value = {"id": 4, "notes": "updated", "is_active": 1}
    conn = MagicMock()
    service = AssessmentService()
    monkeypatch.setattr(service, "_connection", MagicMock(return_value=conn))
    monkeypatch.setattr(
        "sales_coach.app.services.assessment_service.AssessmentRepository",
        MagicMock(return_value=repo),
    )

    result = service.update_assessment_with_reflection(
        4,
        {"summary": {"good": "clear"}, "scores": {"overall": 82}},
    )

    assert result["id"] == 4
    repo.get_active_or_404.assert_called_once_with(4)
    update_payload = repo.update.call_args.args[1]
    notes = json.loads(update_payload["notes"])
    assert notes["reflection_summary"] == {"good": "clear"}
    assert notes["scores"] == {"overall": 82}
    conn.close.assert_called_once_with()


def test_update_no_changes_returns_existing_row(monkeypatch):
    repo = MagicMock()
    repo.get_by_id.return_value = {"id": 7, "trainee_name": "Wang", "is_active": 1}
    conn = MagicMock()
    service = AssessmentService()
    monkeypatch.setattr(service, "_connection", MagicMock(return_value=conn))
    monkeypatch.setattr(
        "sales_coach.app.services.assessment_service.AssessmentRepository",
        MagicMock(return_value=repo),
    )

    result = service.update(7, AssessmentUpdate())

    assert result["trainee_name"] == "Wang"
    repo.update.assert_not_called()
    conn.close.assert_called_once_with()
