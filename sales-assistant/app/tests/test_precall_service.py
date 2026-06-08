import urllib.error
from unittest.mock import MagicMock

from sales_assistant.app.precall_router import PrecallRequest
from sales_assistant.app.services.precall_service import PrecallService


def test_precall_uses_ai_reply_when_gateway_returns_valid_json(monkeypatch):
    service = PrecallService(db=object())
    gather = MagicMock(return_value="HCP信息：姓名=Dr. Li")
    call_ai = MagicMock(
        return_value={
            "reply": (
                '{"basic_info":"known","prescription_tendency":"stable",'
                '"recent_research":"trial","history_summary":"visited",'
                '"talking_points":["data"],"suggested_approach":"academic"}'
            )
        }
    )
    monkeypatch.setattr(service, "_gather_db_context", gather)
    monkeypatch.setattr(service, "_call_ai_gateway", call_ai)
    body = PrecallRequest(customer_name="Dr. Li", hospital="City Hospital")

    result = service.precall(body, auth_header="Bearer token")

    gather.assert_called_once_with("Dr. Li", "City Hospital")
    call_ai.assert_called_once_with("Bearer token", body, "HCP信息：姓名=Dr. Li")
    assert result["customer_name"] == "Dr. Li"
    assert result["brief"]["basic_info"] == "known"
    assert result["brief"]["talking_points"] == ["data"]


def test_precall_falls_back_when_gateway_fails(monkeypatch):
    service = PrecallService(db=object())
    monkeypatch.setattr(service, "_gather_db_context", MagicMock(return_value=""))
    monkeypatch.setattr(
        service,
        "_call_ai_gateway",
        MagicMock(side_effect=urllib.error.URLError("offline")),
    )
    body = PrecallRequest(customer_name="Dr. Wang", hospital=None)

    result = service.precall(body, auth_header="Bearer token")

    assert result["hospital"] is None
    assert "Dr. Wang" in result["brief"]["basic_info"]
    assert result["brief"]["talking_points"]


def test_parse_brief_falls_back_for_invalid_json():
    service = PrecallService(db=object())
    body = PrecallRequest(customer_name="Dr. Chen", hospital="North Hospital")

    brief = service._parse_brief("not-json", body)

    assert "Dr. Chen" in brief["basic_info"]
    assert brief["suggested_approach"]
