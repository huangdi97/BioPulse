"""异常检测路由：异常规则与告警的CRUD接口。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status

from sales_assistant.app.services.anomaly_service import AnomalyService
from shared.auth_scope import require_scope
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


@router.post("/anomaly/rules", summary="创建规则", description="创建异常检测规则")
def create_rule(
    body: RuleCreate,
    service: AnomalyService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    """创建rule。"""
    user_id = int(current_user["sub"])
    row_id = service.create_rule(body, user_id)
    return JSONResponse(
        content=success(data={"id": row_id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/anomaly/rules", summary="规则列表", description="获取异常检测规则列表")
def list_rules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    metric: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    service: AnomalyService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
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


@router.patch("/anomaly/rules/{rule_id}", summary="更新规则", description="更新指定异常检测规则")
def update_rule(
    rule_id: int,
    body: RuleUpdate,
    service: AnomalyService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """更新rule。"""
    row = service.update_rule(rule_id, body)
    return success(data=row)


@router.delete("/anomaly/rules/{rule_id}", summary="删除规则", description="删除指定异常检测规则")
def delete_rule(
    rule_id: int,
    service: AnomalyService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """删除rule。"""
    service.delete_rule(rule_id)
    return success(message="deleted")


@router.post("/anomaly/check", summary="异常检查", description="执行异常检测并生成告警")
def check_anomalies(
    service: AnomalyService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """检查anomalies。"""
    created = service.check_anomalies()
    return success(data={"alerts_created": created})


@router.get("/anomaly/alerts", summary="告警列表", description="获取异常告警列表")
def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    service: AnomalyService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
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


@router.patch("/anomaly/alerts/{alert_id}", summary="更新告警", description="更新指定异常告警状态")
def update_alert(
    alert_id: int,
    body: AlertUpdate,
    service: AnomalyService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """更新alert。"""
    user_id = int(current_user["sub"])
    row = service.update_alert(alert_id, body, user_id)
    return success(data=row)


@router.get("/anomaly/stats", summary="异常统计", description="获取异常检测统计数据")
def anomaly_stats(
    service: AnomalyService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """anomaly stats。"""
    data = service.anomaly_stats()
    return success(data=data)
