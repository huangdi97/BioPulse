from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status

from sales_assistant.app.services.anomaly_service import AnomalyService
from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success

router = APIRouter(tags=["anomaly"])


class RuleCreate(BaseModel):
    rule_name: Optional[str] = None
    metric: Optional[str] = None
    operator: Optional[str] = None
    threshold: Optional[float] = None
    severity: Optional[str] = "medium"
    description: Optional[str] = None


class RuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    metric: Optional[str] = None
    operator: Optional[str] = None
    threshold: Optional[float] = None
    severity: Optional[str] = None
    description: Optional[str] = None


class AlertUpdate(BaseModel):
    status: str
    resolved_by: Optional[int] = None


@router.post("/anomaly/rules")
def create_rule(
    body: RuleCreate,
    service: AnomalyService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    """创建rule。"""
    user_id = int(current_user["sub"])
    row_id = service.create_rule(body, user_id)
    return JSONResponse(
        content=success(data={"id": row_id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/anomaly/rules")
def list_rules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    metric: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    service: AnomalyService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse]:
    """获取rules。"""
    total, total_pages, rows = service.list_rules(page, page_size, metric, severity)
    items = [dict(r) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.patch("/anomaly/rules/{rule_id}")
def update_rule(
    rule_id: int,
    body: RuleUpdate,
    service: AnomalyService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """更新rule。"""
    row = service.update_rule(rule_id, body)
    return success(data=row)


@router.delete("/anomaly/rules/{rule_id}")
def delete_rule(
    rule_id: int,
    service: AnomalyService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """删除rule。"""
    service.delete_rule(rule_id)
    return success(message="deleted")


@router.post("/anomaly/check")
def check_anomalies(
    service: AnomalyService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """检查anomalies。"""
    created = service.check_anomalies()
    return success(data={"alerts_created": created})


@router.get("/anomaly/alerts")
def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    service: AnomalyService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse]:
    """获取alerts。"""
    total, total_pages, rows = service.list_alerts(page, page_size, severity, status)
    items = [dict(r) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.patch("/anomaly/alerts/{alert_id}")
def update_alert(
    alert_id: int,
    body: AlertUpdate,
    service: AnomalyService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """更新alert。"""
    user_id = int(current_user["sub"])
    row = service.update_alert(alert_id, body, user_id)
    return success(data=row)


@router.get("/anomaly/stats")
def anomaly_stats(
    service: AnomalyService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """anomaly stats。"""
    data = service.anomaly_stats()
    return success(data=data)
