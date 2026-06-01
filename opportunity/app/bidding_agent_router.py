from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status

from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success
from opportunity.app.services.bidding_agent_service import BiddingAgentService

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


@router.post("/bidding/configs", status_code=status.HTTP_201_CREATED)
def create_agent_config(
    body: AgentConfigCreate,
    service: BiddingAgentService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    user_id = int(current_user["sub"])
    new_id = service.create_agent_config(body, user_id)
    return JSONResponse(
        content=success(data={"id": new_id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/bidding/configs")
def list_agent_configs(
    service: BiddingAgentService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    rows = service.list_agent_configs()
    return success(data=[AgentConfigOut(**r) for r in rows])


@router.patch("/bidding/configs/{config_id}")
def update_agent_config(
    config_id: int,
    body: AgentConfigUpdate,
    service: BiddingAgentService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    updated = service.update_agent_config(config_id, body)
    return success(data=AgentConfigOut(**updated))


@router.delete("/bidding/configs/{config_id}")
def delete_agent_config(
    config_id: int,
    service: BiddingAgentService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    service.delete_agent_config(config_id)
    return success(message="deleted")


@router.post("/bidding/trigger-scan")
def trigger_scan(
    request: Request,
    service: BiddingAgentService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    auth_header = request.headers.get("Authorization", "")
    result = service.trigger_scan(auth_header)
    return success(data=TriggerScanOut(**result))


@router.get("/bidding/agent-status")
def agent_status(
    service: BiddingAgentService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    result = service.get_agent_status()
    return success(data=AgentStatusOut(**result))


@router.get("/bidding/agent-logs")
def agent_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: BiddingAgentService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse]:
    items, total, page, page_size, total_pages = service.list_agent_logs(
        page, page_size
    )
    return success(
        data=PaginatedResponse(
            items=[AgentLogOut(**i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.post("/bidding/{bidding_id}/auto-analyze")
def auto_analyze_bidding(
    bidding_id: int,
    request: Request,
    service: BiddingAgentService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    auth_header = request.headers.get("Authorization", "")
    analysis = service.auto_analyze_bidding(bidding_id, auth_header)
    return success(data=analysis)


import sqlite3
from opportunity.app.database import DB_PATH
from opportunity.app.services.bidding_agent_service import BiddingAgentService


class _StandaloneBiddingAgentService(BiddingAgentService):
    def __init__(self, db):
        self.db = db


def schedule_bidding_scan():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        service = _StandaloneBiddingAgentService(conn)
        service.run_scheduled_scan()
        conn.close()
    except Exception:
        pass


from apscheduler.schedulers.background import BackgroundScheduler

bidding_scheduler = BackgroundScheduler()


def start_bidding_scheduler():
    if not bidding_scheduler.get_jobs():
        bidding_scheduler.add_job(schedule_bidding_scan, "interval", hours=6)
        bidding_scheduler.start()
