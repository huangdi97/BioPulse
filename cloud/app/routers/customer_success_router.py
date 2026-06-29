"""客户成功路由。"""

from typing import Any

from fastapi import APIRouter, Depends

from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(
    prefix="/api/v1/customer-success",
    tags=["customer_success"],
    dependencies=[Depends(require_scope("admin"))],
)


@router.get("/health")
def health() -> Any:
    return success(message="customer success service is healthy")


@router.get("/usage")
def usage() -> Any:
    return success(
        data={
            "total_users": 0,
            "active_users": 0,
            "feature_usage": {},
        }
    )


@router.get("/at-risk")
def at_risk() -> Any:
    return success(
        data={
            "at_risk_accounts": [],
            "total_at_risk": 0,
        }
    )


@router.get("/nps")
def nps() -> Any:
    return success(
        data={
            "current_score": 0,
            "responses": [],
            "trend": [],
        }
    )
