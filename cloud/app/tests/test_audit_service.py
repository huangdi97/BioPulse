from cloud.app.services.audit_service import AuditService


class TestAuditService:
    def test_log_audit(self):
        svc = AuditService()
        svc.log("test_action", "test_detail")
