from fastapi import APIRouter, Depends
from pydantic import BaseModel

from shared.auth import get_current_user
from cloud.app.dependencies import get_db
from cloud.app.services.compliance_enforcer import ComplianceEnforcer

router = APIRouter(prefix="/api/compliance/enforce", tags=["合规"])


class VisitCheckRequest(BaseModel):
    visit_data: dict


@router.post("")
def enforce_visit(
    body: VisitCheckRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    enforcer = ComplianceEnforcer(db)
    violations = enforcer.check_visit(body.visit_data)
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


@router.get("/rules")
def list_rules(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    enforcer = ComplianceEnforcer(db)
    return {"rules": enforcer.get_l1_rules()}
