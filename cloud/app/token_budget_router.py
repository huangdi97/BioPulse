"""Token budget management router.

Provides admin endpoints for querying and updating token budget
configurations, retrieving usage reports, and listing alerts.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from cloud.app.services.token_budget_service import TokenBudgetService
from shared.base import success

router = APIRouter(prefix="/admin/tokens", tags=["Token 管理"])


class UpdateBudgetRequest(BaseModel):
    model: str
    max_tokens_per_day: Optional[int] = None
    max_tokens_per_request: Optional[int] = None
    alert_threshold: Optional[float] = None


@router.get("/budget/{user_id}")
def get_budget(
    user_id: int,
    model: str = Query("deepseek-v4-pro", description="模型名称"),
    service: TokenBudgetService = Depends(),
) -> Any:
    """获取指定用户和模型的预算配置。"""
    return success(data=service.get_budget(user_id, model))


@router.put("/budget/{user_id}")
def update_budget(
    user_id: int,
    body: UpdateBudgetRequest,
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


@router.get("/usage/{user_id}")
def get_usage_report(
    user_id: int,
    days: int = Query(30, ge=1, le=365, description="回溯天数"),
    service: TokenBudgetService = Depends(),
) -> Any:
    """获取指定用户的使用报告。"""
    return success(data=service.get_usage_report(user_id, days))


@router.get("/alerts")
def list_alerts(
    service: TokenBudgetService = Depends(),
) -> Any:
    """获取所有告警配置列表。"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    configs = service.list_alert_configs()
    alerts = []
    for cfg in configs:
        row = service.db.execute(
            "SELECT COALESCE(SUM(tokens), 0) AS total FROM token_usage WHERE user_id=? AND model=? AND usage_date=?",
            (cfg["user_id"], cfg["model"], today),
        ).fetchone()
        daily_used = row["total"] if row else 0
        limit_today = cfg["max_tokens_per_day"]
        ratio = daily_used / limit_today if limit_today > 0 else 0
        if ratio >= cfg["alert_threshold"]:
            alerts.append(
                {
                    "user_id": cfg["user_id"],
                    "model": cfg["model"],
                    "daily_used": daily_used,
                    "daily_limit": limit_today,
                    "usage_ratio": round(ratio, 4),
                    "threshold": cfg["alert_threshold"],
                    "date": today,
                }
            )
    return success(data=alerts)
