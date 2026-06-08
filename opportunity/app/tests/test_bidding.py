from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from opportunity.app.bidding_router import BiddingCreate, BiddingUpdate
from opportunity.app.services.bidding_service import BiddingService


def test_create_bidding_passes_body_and_audit_fields(monkeypatch):
    repo = MagicMock()
    repo.create.return_value = 42
    repo_cls = MagicMock(return_value=repo)
    monkeypatch.setattr("opportunity.app.services.bidding_service.BiddingInfoRepository", repo_cls)

    service = BiddingService()
    service.db = object()
    body = BiddingCreate(title="Hospital Tender", hospital="City Hospital")

    new_id = service.create_bidding(body, user_id=7)

    assert new_id == 42
    repo_cls.assert_called_once_with(service.db)
    data, kwargs = repo.create.call_args.args[0], repo.create.call_args.kwargs
    assert data["title"] == "Hospital Tender"
    assert data["hospital"] == "City Hospital"
    assert kwargs["extra"]["created_by"] == 7
    assert "created_at" in kwargs["extra"]
    assert "updated_at" in kwargs["extra"]


def test_list_bidding_builds_expected_filters(monkeypatch):
    repo = MagicMock()
    repo.paginate.return_value = (1, 1, [{"id": 1, "title": "Tender"}])
    monkeypatch.setattr(
        "opportunity.app.services.bidding_service.BiddingInfoRepository",
        MagicMock(return_value=repo),
    )

    service = BiddingService()
    service.db = object()
    result = service.list_bidding(
        page=2,
        page_size=5,
        status_val="new",
        hospital="General",
        department="Cardiology",
        product_category="Device",
    )

    assert result == (1, 1, [{"id": 1, "title": "Tender"}])
    repo.paginate.assert_called_once_with(
        2,
        5,
        conditions=[
            "is_active = 1",
            "status = ?",
            "hospital LIKE ?",
            "department LIKE ?",
            "product_category LIKE ?",
        ],
        params=["new", "%General%", "%Cardiology%", "%Device%"],
        order_by="id DESC",
    )


def test_update_bidding_returns_existing_row_when_no_updates(monkeypatch):
    row = {"id": 3, "title": "Existing", "is_active": 1}
    repo = MagicMock()
    repo.get_by_id.return_value = row
    monkeypatch.setattr(
        "opportunity.app.services.bidding_service.BiddingInfoRepository",
        MagicMock(return_value=repo),
    )

    service = BiddingService()
    service.db = object()
    result = service.update_bidding(3, BiddingUpdate())

    assert result == row
    repo.update.assert_not_called()


def test_get_bidding_raises_404_for_inactive_record(monkeypatch):
    repo = MagicMock()
    repo.get_by_id.return_value = {"id": 9, "title": "Old", "is_active": 0}
    monkeypatch.setattr(
        "opportunity.app.services.bidding_service.BiddingInfoRepository",
        MagicMock(return_value=repo),
    )

    service = BiddingService()
    service.db = object()

    with pytest.raises(HTTPException) as exc:
        service.get_bidding(9)

    assert exc.value.status_code == 404
