from cloud.app.services.approval_service import ApprovalService


class TestApprovalService:
    def test_submit_quotation_missing_fields(self):
        svc = ApprovalService()
        result = svc.submit_quotation({})
        assert isinstance(result, dict)
