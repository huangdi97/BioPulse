from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette import status

from shared.auth_scope import require_scope
from shared.base import success
from shared.compliance import check_content
from cloud.app.services.compliance_service import ComplianceService

router = APIRouter(prefix="/compliance", tags=["compliance"])


class CheckRequest(BaseModel):
    content: str
    rules: List[dict]


class CheckResponse(BaseModel):
    passed: bool
    violations: List[str]
    score: float


class RuleCreate(BaseModel):
    name: str
    category: str
    keyword: str
    max_value: Optional[float] = None


class RuleResponse(BaseModel):
    id: int
    name: str
    category: str
    keyword: str
    max_value: Optional[float]


@router.post("/check")
def check(request: CheckRequest) -> Any:
    """Check content against a set of compliance rules without authentication."""
    result = check_content(request.content, request.rules)
    return success(data=result.model_dump())


@router.post("/rules")
def create_rule(
    body: RuleCreate,
    current_user: dict = Depends(require_scope("visit")),
    service: ComplianceService = Depends(),
) -> Any:
    """Create a new compliance rule."""
    user_id = int(current_user["sub"])
    result = service.create_rule(
        name=body.name, category=body.category,
        keyword=body.keyword, max_value=body.max_value,
        created_by=user_id,
    )
    return success(data=result)


@router.get("/rules")
def list_rules(
    current_user: dict = Depends(require_scope("visit")),
    service: ComplianceService = Depends(),
) -> Any:
    """List all compliance rules."""
    return success(data=service.list_rules())


@router.delete("/rules/{rule_id:int}")
def delete_rule(
    rule_id: int,
    current_user: dict = Depends(require_scope("visit")),
    service: ComplianceService = Depends(),
) -> Any:
    """Delete a compliance rule by ID."""
    service.delete_rule(rule_id)
    return success()
