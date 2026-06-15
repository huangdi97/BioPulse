from cloud.app.compliance.service import ComplianceService


class TestComplianceService:
    def test_check_compliance(self):
        svc = ComplianceService()
        result = svc.check({"action": "test"})
        assert isinstance(result, dict)
