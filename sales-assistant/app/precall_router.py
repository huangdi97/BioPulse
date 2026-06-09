"""访前准备路由：拜访简报生成API。"""

from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from sales_assistant.app.schemas.call_report import CallReport, PostCallSummary, PreCallBrief, VisitExecution
from sales_assistant.app.services.call_report_service import (
    get_call_report,
    update_execution,
    update_precall,
    update_summary,
)
from sales_assistant.app.services.precall_service import PrecallService
from shared.auth_scope import require_scope
from shared.base import ApiResponse, success

router = APIRouter(tags=["Pre-call Brief"])


class PrecallRequest(BaseModel):
    customer_name: str
    hospital: str | None = None
    extra_context: str | None = None


class BriefData(BaseModel):
    basic_info: str
    prescription_tendency: str
    recent_research: str
    history_summary: str
    talking_points: list[str]
    suggested_approach: str


class PrecallResponse(BaseModel):
    customer_name: str
    hospital: str | None
    brief: BriefData


@router.post("/precall", response_model=ApiResponse[PrecallResponse], summary="生成简报", description="生成访前准备简报", tags=["情报"])
def precall(
    request: Request,
    body: PrecallRequest,
    service: PrecallService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> Any:
    """precall。"""
    auth_header = request.headers.get("Authorization", "")
    result = service.precall(body, auth_header)
    return success(
        PrecallResponse(
            customer_name=result["customer_name"],
            hospital=result["hospital"],
            brief=BriefData(**result["brief"]),
        )
    )


@router.get("/precall", summary="获取简报", description="获取访前准备简报", tags=["情报"])
def get_precall() -> Any:
    """precall。"""
    return {}


@router.get("/api/precall/{visit_id}", response_model=CallReport, summary="获取三段式Call Report", tags=["拜访"])
def get_visit_call_report(visit_id: str) -> CallReport:
    return get_call_report(visit_id)


@router.put("/api/precall/{visit_id}/brief", response_model=CallReport, summary="更新访前准备", tags=["拜访"])
def put_precall_brief(visit_id: str, body: PreCallBrief) -> CallReport:
    return update_precall(visit_id, body)


@router.put("/api/precall/{visit_id}/execution", response_model=CallReport, summary="更新拜访执行", tags=["拜访"])
def put_visit_execution(visit_id: str, body: VisitExecution) -> CallReport:
    return update_execution(visit_id, body)


@router.put("/api/precall/{visit_id}/summary", response_model=CallReport, summary="更新拜访总结", tags=["拜访"])
def put_postcall_summary(visit_id: str, body: PostCallSummary) -> CallReport:
    return update_summary(visit_id, body)
