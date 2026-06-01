from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from starlette import status

from shared.auth_scope import require_scope
from shared.base import success
from cloud.app.services.marketplace_service import MarketplaceService

router = APIRouter(prefix="/marketplace", tags=["Marketplace & Analytics"])


class MetricLog(BaseModel):
    agent_role: str
    metric_type: str
    metric_value: float
    metric_unit: str = ""
    period_start: str = ""
    period_end: str = ""


class BenchmarkGenerate(BaseModel):
    report_name: str
    report_type: str = ""
    period: str = ""


class MarketplacePublish(BaseModel):
    item_name: str
    description: str = ""
    agent_config: dict = {}
    category: str = ""
    price_model: str = "free"


@router.post("/metrics/log", status_code=status.HTTP_201_CREATED)
def log_metric(
    body: MetricLog,
    current_user: dict = Depends(require_scope("visit")),
    service: MarketplaceService = Depends(),
) -> Any:
    return success(
        data=service.log_metric(
            body.agent_role,
            body.metric_type,
            body.metric_value,
            body.metric_unit,
            body.period_start,
            body.period_end,
        )
    )


@router.get("/metrics/dashboard")
def metrics_dashboard(
    current_user: dict = Depends(require_scope("visit")),
    service: MarketplaceService = Depends(),
    agent_role: Optional[str] = Query(None),
) -> Any:
    return success(data=service.metrics_dashboard(agent_role=agent_role))


@router.post("/benchmark/generate", status_code=status.HTTP_201_CREATED)
def generate_benchmark(
    body: BenchmarkGenerate,
    current_user: dict = Depends(require_scope("visit")),
    service: MarketplaceService = Depends(),
) -> Any:
    return success(
        data=service.generate_benchmark(body.report_name, body.report_type, body.period)
    )


@router.get("/benchmark/list")
def list_benchmarks(
    current_user: dict = Depends(require_scope("visit")),
    service: MarketplaceService = Depends(),
    report_type: Optional[str] = Query(None),
) -> Any:
    return success(data=service.list_benchmarks(report_type=report_type))


@router.post("/items/publish", status_code=status.HTTP_201_CREATED)
def publish_item(
    body: MarketplacePublish,
    current_user: dict = Depends(require_scope("visit")),
    service: MarketplaceService = Depends(),
) -> Any:
    return success(
        data=service.publish_item(
            body.item_name,
            body.description,
            body.agent_config,
            body.category,
            body.price_model,
            str(current_user.get("sub", "unknown")),
        )
    )


@router.get("/items/discover")
def discover_items(
    current_user: dict = Depends(require_scope("visit")),
    service: MarketplaceService = Depends(),
    category: Optional[str] = Query(None),
    price_model: Optional[str] = Query(None),
    enabled: Optional[int] = Query(None),
) -> Any:
    return success(
        data=service.discover_items(
            category=category, price_model=price_model, enabled=enabled
        )
    )
