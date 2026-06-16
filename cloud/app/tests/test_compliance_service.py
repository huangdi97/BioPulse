from cloud.app.compliance.service import ComplianceService


class TestComplianceService:
    def test_check_compliance(self):
        svc = ComplianceService()
        result = svc.dashboard()
        assert isinstance(result, dict)
