from assistant.app.services.visit_service import VisitService


class TestVisitService:
    def test_offline_visit_score_default(self):
        svc = VisitService()
        result = svc._offline_visit_score({})
        assert result["source"] == "offline_rule"
        assert 0 <= result["score"] <= 100
        assert result["level"] in ("low", "medium", "high")
        assert "breakdown" in result

    def test_offline_visit_score_high_value(self):
        svc = VisitService()
        result = svc._offline_visit_score(
            {
                "hcp_value": "high",
                "previous_visits": 3,
                "has_conflict": False,
                "scheduled_date": "2026-06-10",
            }
        )
        assert result["score"] >= 70

    def test_get_visit_not_found(self):
        svc = VisitService()
        try:
            svc.get_visit(99999)
            assert False, "expected 404"
        except Exception as e:
            assert hasattr(e, "status_code") and e.status_code == 404

    def test_get_visit_score_nonexistent(self):
        svc = VisitService()
        try:
            svc.get_visit_score(99999)
            assert False, "expected 404"
        except Exception as e:
            assert hasattr(e, "status_code") and e.status_code == 404
