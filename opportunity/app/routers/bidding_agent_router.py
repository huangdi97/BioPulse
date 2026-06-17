"""招投标Agent API 端点。"""

import logging
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status

from opportunity.app.services.bidding_agent_service import BiddingAgentService
from shared.auth_scope import require_scope
from shared.base import ApiResponse, PaginatedResponse, success

logger = logging.getLogger(__name__)

router = APIRouter(tags=["bidding-agent"])


class AgentConfigCreate(BaseModel):
    name: str
    keywords: Optional[str] = None
    regions: Optional[str] = None
    auto_parse: Optional[int] = 1
    auto_notify: Optional[int] = 1
    notify_to: Optional[str] = None
    schedule_interval: Optional[int] = 360


class AgentConfigUpdate(BaseModel):
    name: Optional[str] = None
    keywords: Optional[str] = None
    regions: Optional[str] = None
    auto_parse: Optional[int] = None
    auto_notify: Optional[int] = None
    notify_to: Optional[str] = None
    schedule_interval: Optional[int] = None
    is_active: Optional[int] = None


class AgentConfigOut(BaseModel):
    id: int
    name: str
    keywords: Optional[str] = None
    regions: Optional[str] = None
    auto_parse: int = 1
    auto_notify: int = 1
    notify_to: Optional[str] = None
    schedule_interval: int = 360
    is_active: int = 1
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AgentLogOut(BaseModel):
    id: int
    config_id: Optional[int] = None
    run_status: Optional[str] = None
    items_found: int = 0
    items_parsed: int = 0
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: Optional[str] = None


class TriggerScanOut(BaseModel):
    total_found: int
    total_parsed: int
    errors: list


class AgentStatusOut(BaseModel):
    last_run: Optional[str] = None
    total_runs: int
    success_rate: float


class AutoAnalyzeOut(BaseModel):
    opportunity_assessment: str
    product_suggestions: list
    risk_factors: list
    next_steps: list


@router.post("/bidding/configs", summary="创建配置", description="创建招投标代理配置", status_code=status.HTTP_201_CREATED)
def create_agent_config(
    body: AgentConfigCreate,
    service: BiddingAgentService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    """创建代理配置。"""
    user_id = int(current_user["sub"])
    new_id = service.create_agent_config(body, user_id)
    return JSONResponse(
        content=success(data={"id": new_id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/bidding/configs", summary="配置列表", description="获取招投标代理配置列表")
def list_agent_configs(
    service: BiddingAgentService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """获取代理配置列表。"""
    rows = service.list_agent_configs()
    return success(data=[AgentConfigOut(**r) for r in rows])


@router.patch("/bidding/configs/{config_id}", summary="更新配置", description="更新招投标代理配置信息")
def update_agent_config(
    config_id: int,
    body: AgentConfigUpdate,
    service: BiddingAgentService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """更新代理配置。"""
    updated = service.update_agent_config(config_id, body)
    return success(data=AgentConfigOut(**updated))


@router.delete("/bidding/configs/{config_id}", summary="删除配置", description="删除招投标代理配置")
def delete_agent_config(
    config_id: int,
    service: BiddingAgentService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """删除代理配置。"""
    service.delete_agent_config(config_id)
    return success(message="deleted")


@router.post("/bidding/trigger-scan", summary="触发扫描", description="触发招标信息扫描任务")
def trigger_scan(
    request: Request,
    service: BiddingAgentService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """触发扫描任务。"""
    auth_header = request.headers.get("Authorization", "")
    result = service.trigger_scan(auth_header)
    return success(data=TriggerScanOut(**result))


@router.get("/bidding/agent-status", summary="代理状态", description="获取招投标代理的运行状态")
def agent_status(
    service: BiddingAgentService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """获取代理运行状态。"""
    result = service.get_agent_status()
    return success(data=AgentStatusOut(**result))


@router.get("/bidding/agent-logs", summary="运行日志", description="获取代理运行日志列表（分页）")
def agent_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: BiddingAgentService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[PaginatedResponse]:
    """获取代理运行日志列表（分页）。"""
    items, total, page, page_size, total_pages = service.list_agent_logs(page, page_size)
    return success(
        data=PaginatedResponse(
            items=[AgentLogOut(**i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.post("/bidding/{bidding_id}/auto-analyze", summary="自动分析", description="自动分析指定的招标信息")
def auto_analyze_bidding(
    bidding_id: int,
    request: Request,
    service: BiddingAgentService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """自动分析招标信息。"""
    auth_header = request.headers.get("Authorization", "")
    analysis = service.auto_analyze_bidding(bidding_id, auth_header)
    return success(data=analysis)


def schedule_bidding_scan():
    """定时执行招标扫描任务（由调度器调用）。"""
    try:
        service = BiddingAgentService()
        service.run_scheduled_scan()
    except Exception:
        logger.exception("投标路由异常")


bidding_scheduler = BackgroundScheduler()


def start_bidding_scheduler():
    """启动定时调度器，每 6 小时执行一次招标扫描。"""
    if not bidding_scheduler.get_jobs():
        bidding_scheduler.add_job(schedule_bidding_scan, "interval", hours=6)
        bidding_scheduler.start()
