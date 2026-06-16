"""合规检查路由。"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from starlette import status

from cloud.app.compliance.service import ComplianceService
from shared.auth_scope import require_scope
from shared.base import success
from shared.compliance import check_content

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


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    keyword: Optional[str] = None
    max_value: Optional[float] = None


class RuleResponse(BaseModel):
    id: int
    name: str
    category: str
    keyword: str
    max_value: Optional[float]


@router.post("/check", summary="检查内容合规性", description="对内容进行合规规则检查，无需认证", tags=["compliance"])
def check(request: CheckRequest) -> Any:
    """Check content against a set of compliance rules without authentication."""
    result = check_content(request.content, request.rules)
    return success(data=result.model_dump())


@router.post("/rules", status_code=status.HTTP_201_CREATED, summary="创建合规规则", description="创建一条新的合规检查规则", tags=["compliance"])
def create_rule(
    body: RuleCreate,
    current_user: dict = Depends(require_scope("visit")),
    service: ComplianceService = Depends(),
) -> Any:
    """Create a new compliance rule."""
    user_id = int(current_user["sub"])
    result = service.create_rule(
        name=body.name,
        category=body.category,
        keyword=body.keyword,
        max_value=body.max_value,
        created_by=user_id,
    )
    return success(data=result)


@router.get("/rules", summary="列出所有合规规则", description="获取所有合规规则的列表", tags=["compliance"])
def list_rules(
    current_user: dict = Depends(require_scope("visit")),
    service: ComplianceService = Depends(),
) -> Any:
    """List all compliance rules."""
    return success(data=service.list_rules())


@router.patch("/rules/{rule_id:int}", summary="更新合规规则", description="更新指定规则的参数", tags=["compliance"])
def update_rule(
    rule_id: int,
    body: RuleUpdate,
    current_user: dict = Depends(require_scope("visit")),
    service: ComplianceService = Depends(),
) -> Any:
    """Update a compliance rule by ID."""
    result = service.update_rule(
        rule_id=rule_id,
        name=body.name,
        category=body.category,
        keyword=body.keyword,
        max_value=body.max_value,
    )
    return success(data=result)


@router.delete("/rules/{rule_id:int}", summary="删除合规规则", description="根据规则ID删除指定的合规规则", tags=["compliance"])
def delete_rule(
    rule_id: int,
    current_user: dict = Depends(require_scope("visit")),
    service: ComplianceService = Depends(),
) -> Any:
    """Delete a compliance rule by ID."""
    service.delete_rule(rule_id)
    return success()
