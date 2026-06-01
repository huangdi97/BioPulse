from cloud.app.services.base import BaseService
from cloud.app.services.compliance_enforcer import ComplianceEnforcer


class EnforcerService(BaseService):
    def check_visit(self, visit_data: dict) -> dict:
        enforcer = ComplianceEnforcer(self.db)
        violations = enforcer.check_visit(visit_data)
        return {
            "violations": [
                {
                    "rule_code": v.rule_code,
                    "rule_name": v.rule_name,
                    "severity": v.severity,
                    "action": v.action,
                    "detail": v.detail,
                }
                for v in violations
            ],
            "passed": len(violations) == 0,
        }

    def list_rules(self) -> dict:
        enforcer = ComplianceEnforcer(self.db)
        return {"rules": enforcer.get_l1_rules()}
