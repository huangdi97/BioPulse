from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from sales_assistant.app.sales_assistant_hcp_router import HcpCreate, HcpUpdate
from sales_assistant.app.services.hcp_service import HcpService


def test_create_hcp_passes_audit_fields(monkeypatch):
    repo = MagicMock()
    repo.create.return_value = 11
    monkeypatch.setattr(
        "sales_assistant.app.services.hcp_service.HcpRepository",
        MagicMock(return_value=repo),
    )

    service = HcpService(db=object())
    result = service.create_hcp(HcpCreate(name="Dr. Zhao", hospital="Tongji"), user_id=4)

    assert result == 11
    data, kwargs = repo.create.call_args.args[0], repo.create.call_args.kwargs
    assert data["name"] == "Dr. Zhao"
    assert kwargs["extra"]["created_by"] == 4
    assert "updated_at" in kwargs["extra"]


def test_list_hcps_builds_filters(monkeypatch):
    repo = MagicMock()
    repo.paginate.return_value = (0, 1, [])
    monkeypatch.setattr(
        "sales_assistant.app.services.hcp_service.HcpRepository",
        MagicMock(return_value=repo),
    )

    service = HcpService(db=object())
    result = service.list_hcps(
        page=3,
        page_size=15,
        name="Li",
        hospital="Union",
        department="Oncology",
    )

    assert result == (0, 1, [])
    repo.paginate.assert_called_once_with(
        3,
        15,
        ["is_active = 1", "name LIKE ?", "hospital LIKE ?", "department LIKE ?"],
        ["%Li%", "%Union%", "%Oncology%"],
    )


def test_update_hcp_updates_only_supplied_fields(monkeypatch):
    repo = MagicMock()
    repo.get_by_id.side_effect = [
        {"id": 5, "name": "Old", "is_active": 1},
        {"id": 5, "name": "New", "tier": "A", "is_active": 1},
    ]
    monkeypatch.setattr(
        "sales_assistant.app.services.hcp_service.HcpRepository",
        MagicMock(return_value=repo),
    )

    service = HcpService(db=object())
    updated = service.update_hcp(5, HcpUpdate(name="New", tier="A"))

    assert updated["name"] == "New"
    update_payload = repo.update.call_args.args[1]
    assert update_payload["name"] == "New"
    assert update_payload["tier"] == "A"
    assert "hospital" not in update_payload
    assert "updated_at" in update_payload


def test_get_hcp_raises_404_when_inactive(monkeypatch):
    repo = MagicMock()
    repo.get_by_id.return_value = {"id": 6, "name": "Inactive", "is_active": 0}
    monkeypatch.setattr(
        "sales_assistant.app.services.hcp_service.HcpRepository",
        MagicMock(return_value=repo),
    )

    service = HcpService(db=object())

    with pytest.raises(HTTPException) as exc:
        service.get_hcp(6)

    assert exc.value.status_code == 404
