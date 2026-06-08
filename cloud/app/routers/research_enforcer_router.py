"""科研合规路由：科研拜访合规检查与规则查询。"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from cloud.app.services.compliance_enforcer_service import ResearchComplianceEnforcer
from cloud.app.services.research_service import ResearchService
from shared.auth import get_current_user
from shared.auth_scope import require_scope

router = APIRouter(
    prefix="/api/research/compliance",
    tags=["科研线"],
    dependencies=[Depends(require_scope("research"))],
)


class ResearchVisitCheckRequest(BaseModel):
    """科研拜访合规检查请求体。"""

    visit_data: dict


@router.post("/enforce")
def enforce_research_visit(
    body: ResearchVisitCheckRequest,
    current_user: dict = Depends(get_current_user),
):
    db = ResearchService().get_research_db()
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
    db = ResearchService().get_research_db()
    try:
        enforcer = ResearchComplianceEnforcer(db)
        return {"rules": enforcer.get_l1_rules()}
    finally:
        db.close()
