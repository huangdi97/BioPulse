"""异议处理路由：客户异议分析与应答建议API。"""

from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from sales_assistant.app.services.objection_service import ObjectionService
from shared.auth import get_current_user
from shared.base import ApiResponse, success

router = APIRouter(tags=["Objection Handling"])


class ObjectionRequest(BaseModel):
    objection: str
    customer_type: str | None = None
    context: str | None = None


class ObjectionResponse(BaseModel):
    objection: str
    analysis: str
    response_suggestion: str
    key_points: list[str]
    do_not_say: list[str]


@router.post("/objection", response_model=ApiResponse[ObjectionResponse], summary="异议处理", description="处理客户异议并获取应答建议")
def handle_objection(
    request: Request,
    body: ObjectionRequest,
    service: ObjectionService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> Any:
    """handle objection。"""
    auth_header = request.headers.get("Authorization", "")
    result = service.handle_objection(body, auth_header)
    return success(ObjectionResponse(**result))


@router.get("/objections", summary="异议列表", description="获取异议列表")
def list_objections() -> list:
    """获取objections。"""
    return []
