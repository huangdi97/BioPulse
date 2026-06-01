from fastapi import APIRouter, Depends
from pydantic import BaseModel

from shared.auth import get_current_user
from shared.auth_scope import require_scope
from cloud.app.research_database import get_research_db
from cloud.app.services.compliance_enforcer import ResearchComplianceEnforcer

router = APIRouter(
    prefix="/api/research/compliance",
    tags=["科研线"],
    dependencies=[Depends(require_scope("research"))],
)


class ResearchVisitCheckRequest(BaseModel):
    visit_data: dict


@router.post("/enforce")
def enforce_research_visit(
    body: ResearchVisitCheckRequest,
    current_user: dict = Depends(get_current_user),
):
    db = get_research_db()
    try:
        enforcer = ResearchComplianceEnforcer(db)
        violations = enforcer.check_research_visit(body.visit_data)
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
    finally:
        db.close()


@router.get("/enforce/rules")
def list_research_rules(
    current_user: dict = Depends(get_current_user),
):
    db = get_research_db()
    try:
        enforcer = ResearchComplianceEnforcer(db)
        return {"rules": enforcer.get_l1_rules()}
    finally:
        db.close()
