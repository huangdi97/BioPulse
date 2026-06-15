from cloud.app.services.visit_service import VisitService


class TestVisitService:
    def test_record_visit(self):
        svc = VisitService()
        result = svc.record_visit({"rep_id": 1, "hcp_id": 1})
        assert result is not None
