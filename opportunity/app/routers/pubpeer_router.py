"""论文诚信查询 API。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from opportunity.app.services.pubpeer_service import PubpeerService
from shared.auth_scope import require_scope
from shared.base import ApiResponse, ErrorCode, PaginatedResponse, success

router = APIRouter(tags=["pubpeer", "integrity"])


class IntegrityOut(BaseModel):
    id: int
    pubmed_id: Optional[str] = None
    doi: Optional[str] = None
    title: Optional[str] = None
    integrity_score: int = 50
    retraction_warning: int = 0
    concerns: Optional[str] = None
    flags: Optional[str] = None
    checked_at: Optional[str] = None
    check_count: int = 0
    is_active: int = 1
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PubpeerCheckRequest(BaseModel):
    pubmed_id: Optional[str] = None
    doi: Optional[str] = None


class IntegrityCheckOut(BaseModel):
    pubmed_id: Optional[str] = None
    doi: Optional[str] = None
    integrity_score: int
    retraction_warning: bool
    concerns: list
    checked_at: str


@router.post("/research-trails/{trail_id}/check-integrity", summary="诚信检查", description="检查科研轨迹的论文诚信")
def check_trail_integrity(
    trail_id: int,
    request: Request,
    service: PubpeerService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """检查trail integrity。"""
    user_id = int(current_user["sub"])
    auth_header = request.headers.get("Authorization", "")
    result = service.check_trail_integrity(trail_id, auth_header, user_id)
    return success(data=IntegrityCheckOut(**result))


@router.get("/research-trails/{trail_id}/integrity", summary="诚信详情", description="获取科研轨迹的诚信检查结果")
def get_trail_integrity(
    trail_id: int,
    service: PubpeerService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """获取trail integrity。"""
    row = service.get_trail_integrity(trail_id)
    if not row:
        return success(data=None, message="No integrity check found")
    return success(data=IntegrityOut(**row))


@router.post("/pubpeer/check", summary="PubPeer查询", description="通过PubPeer查询论文诚信信息")
def pubpeer_check(
    body: PubpeerCheckRequest,
    request: Request,
    service: PubpeerService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """pubpeer check。"""
    user_id = int(current_user["sub"])
    auth_header = request.headers.get("Authorization", "")
    result = service.pubpeer_check(body, auth_header, user_id)
    if result == "validation_error":
        return ApiResponse(code=ErrorCode.VALIDATION_ERROR, message="Provide pubmed_id or doi")
    return success(data=IntegrityCheckOut(**result))


@router.get("/pubpeer/alerts", summary="诚信警报", description="获取论文诚信警报列表")
def pubpeer_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: PubpeerService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[PaginatedResponse]:
    """pubpeer alerts。"""
    total, total_pages, rows = service.list_alerts(page, page_size)
    items = [IntegrityOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )
