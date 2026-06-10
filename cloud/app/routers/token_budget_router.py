"""Token budget management router.

Provides admin endpoints for querying and updating token budget
configurations, retrieving usage reports, and listing alerts.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from cloud.app.services.token_budget_service import TokenBudgetService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/admin/tokens", tags=["Token 管理"])


class UpdateBudgetRequest(BaseModel):
    model: str
    max_tokens_per_day: Optional[int] = None
    max_tokens_per_request: Optional[int] = None
    alert_threshold: Optional[float] = None


@router.get("/budget/{user_id}", tags=["Token 管理"])
def get_budget(
    user_id: int,
    model: str = Query("deepseek-v4-pro", description="模型名称"),
    service: TokenBudgetService = Depends(),
) -> Any:
    """获取指定用户和模型的预算配置。"""
    return success(data=service.get_budget(user_id, model))


@router.put("/budget/{user_id}", tags=["Token 管理"])
def update_budget(
    user_id: int,
    body: UpdateBudgetRequest,
    _: dict = Depends(require_scope("visit")),
    service: TokenBudgetService = Depends(),
) -> Any:
    """更新指定用户和模型的预算配置。"""
    data = service.update_budget(
        user_id=user_id,
        model=body.model,
        max_tokens_per_day=body.max_tokens_per_day,
        max_tokens_per_request=body.max_tokens_per_request,
        alert_threshold=body.alert_threshold,
    )
    return success(data=data)


@router.get("/usage/{user_id}", tags=["Token 管理"])
def get_usage_report(
    user_id: int,
    days: int = Query(30, ge=1, le=365, description="回溯天数"),
    service: TokenBudgetService = Depends(),
) -> Any:
    """获取指定用户的使用报告。"""
    return success(data=service.get_usage_report(user_id, days))


@router.get("/alerts", tags=["Token 管理"])
def list_alerts(
    service: TokenBudgetService = Depends(),
) -> Any:
    """获取所有告警配置列表。"""
    return success(data=service.get_alerts())
