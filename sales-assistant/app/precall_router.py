"""访前准备路由：拜访简报生成API。"""

from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from sales_assistant.app.services.precall_service import PrecallService
from shared.auth import get_current_user
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


@router.post("/precall", response_model=ApiResponse[PrecallResponse])
def precall(
    request: Request,
    body: PrecallRequest,
    service: PrecallService = Depends(),
    current_user: dict = Depends(get_current_user),
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


@router.get("/precall")
def get_precall() -> Any:
    """precall。"""
    return {}
