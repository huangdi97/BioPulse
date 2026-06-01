from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from starlette import status

from cloud.app.services.route_service import RouteService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/route", tags=["Route"])


class RuleCreate(BaseModel):
    name: str
    priority: int = 100
    condition_field: str = "keyword"
    condition_operator: str = "contains"
    condition_value: str
    target_role_id: int
    fallback_role_id: Optional[int] = None
    max_tokens: int = 2048
    temperature: float = 0.7


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    priority: Optional[int] = None
    condition_value: Optional[str] = None
    target_role_id: Optional[int] = None
    is_active: Optional[int] = None


class RouteExecute(BaseModel):
    input: str
    context: dict = {}


@router.post("/rules", status_code=status.HTTP_201_CREATED)
def create_rule(
    body: RuleCreate,
    current_user=Depends(require_scope("visit")),
    service: RouteService = Depends(),
):
    row = service.create_rule(
        name=body.name,
        priority=body.priority,
        condition_field=body.condition_field,
        condition_operator=body.condition_operator,
        condition_value=body.condition_value,
        target_role_id=body.target_role_id,
        fallback_role_id=body.fallback_role_id,
        max_tokens=body.max_tokens,
        temperature=body.temperature,
        created_by=int(current_user["sub"]),
    )
    return success(data=row)


@router.get("/rules")
def list_rules(
    current_user=Depends(require_scope("visit")), service: RouteService = Depends()
):
    return success(data=service.list_rules())


@router.patch("/rules/{rule_id}")
def update_rule(
    rule_id: int,
    body: RuleUpdate,
    current_user=Depends(require_scope("visit")),
    service: RouteService = Depends(),
):
    row = service.update_rule(
        rule_id=rule_id,
        name=body.name,
        priority=body.priority,
        condition_value=body.condition_value,
        target_role_id=body.target_role_id,
        is_active=body.is_active,
    )
    return success(data=row)


@router.delete("/rules/{rule_id}")
def delete_rule(
    rule_id: int,
    current_user=Depends(require_scope("visit")),
    service: RouteService = Depends(),
):
    service.delete_rule(rule_id)
    return success()


@router.post("/execute")
def execute_route(
    body: RouteExecute,
    current_user=Depends(require_scope("visit")),
    service: RouteService = Depends(),
):
    result = service.execute_route(
        input_text=body.input,
        uid=int(current_user["sub"]),
        source=body.context.get("source", ""),
    )
    return success(data=result)


@router.get("/logs")
def list_logs(
    role_id: Optional[int] = Query(None),
    source: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(require_scope("visit")),
    service: RouteService = Depends(),
):
    return success(
        data=service.list_logs(
            role_id=role_id,
            source=source,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/logs/{log_id}")
def get_log(
    log_id: int,
    current_user=Depends(require_scope("visit")),
    service: RouteService = Depends(),
):
    return success(data=service.get_log(log_id))


@router.get("/stats")
def get_stats(
    current_user=Depends(require_scope("visit")), service: RouteService = Depends()
):
    return success(data=service.get_stats())


@router.get("/dashboard")
def get_dashboard(
    current_user=Depends(require_scope("visit")), service: RouteService = Depends()
):
    return success(data=service.get_dashboard())
