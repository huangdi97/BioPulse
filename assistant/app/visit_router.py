"""拜访路由模块，定义拜访记录增删改查的 API 端点。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette import status

from assistant.app.services.visit_service import VisitService
from shared.auth_scope import require_scope
from shared.base import ApiResponse, PaginatedResponse, success

router = APIRouter(prefix="/visits", tags=["visits"])


class VisitCreate(BaseModel):
    """Request model for creating a visit record."""

    hcp_id: int
    visit_type: Optional[str] = None
    summary: Optional[str] = Field(None, max_length=2000)
    # outcome: Optional[str] = Field(None, max_length=500)
    detail: Optional[str] = None
    feedback: Optional[str] = None
    next_action: Optional[str] = None
    mood: Optional[str] = None
    is_completed: Optional[int] = 1
    visit_date: Optional[str] = None


class VisitUpdate(BaseModel):
    """Request model for updating a visit record."""

    hcp_id: Optional[int] = None
    visit_type: Optional[str] = None
    summary: Optional[str] = None
    detail: Optional[str] = None
    feedback: Optional[str] = None
    next_action: Optional[str] = None
    mood: Optional[str] = None
    is_completed: Optional[int] = None
    visit_date: Optional[str] = None


class VisitOut(BaseModel):
    """Response model for a visit record."""

    id: int
    hcp_id: int
    visit_type: Optional[str] = None
    summary: Optional[str] = None
    detail: Optional[str] = None
    feedback: Optional[str] = None
    next_action: Optional[str] = None
    mood: Optional[str] = None
    is_completed: int
    visit_date: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[str] = None


@router.post("", summary="创建拜访", description="创建新的拜访记录。")
def create_visit(
    body: VisitCreate,
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    """Create a new visit record."""
    service = VisitService()
    user_id = int(current_user["sub"])
    result = service.create_visit(body, user_id)
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("", summary="查询拜访列表", description="分页查询拜访记录，支持按HCP和类型筛选。")
def list_visits(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    hcp_id: Optional[int] = Query(None),
    visit_type: Optional[str] = Query(None),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[PaginatedResponse[VisitOut]]:
    """List visit records with pagination and filtering."""
    service = VisitService()
    total, total_pages, rows = service.list_visits(
        page=page,
        page_size=page_size,
        hcp_id=hcp_id,
        visit_type=visit_type,
    )
    items = [VisitOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/{visit_id}", summary="获取拜访详情", description="根据ID获取单个拜访记录的详细信息。")
def get_visit(
    visit_id: int,
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[VisitOut]:
    """Get a single visit record by ID."""
    service = VisitService()
    row = service.get_visit(visit_id)
    return success(data=VisitOut(**dict(row)))


@router.patch("/{visit_id}", summary="更新拜访", description="更新指定拜访记录的部分字段信息。")
def update_visit(
    visit_id: int,
    body: VisitUpdate,
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[VisitOut]:
    """Update a visit record."""
    service = VisitService()
    row = service.update_visit(visit_id, body)
    return success(data=VisitOut(**row))


@router.delete("/{visit_id}", summary="删除拜访", description="删除指定的拜访记录。")
def delete_visit(
    visit_id: int,
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """Delete a visit record."""
    service = VisitService()
    service.delete_visit(visit_id)
    return success(message="deleted")


visit_alias_router = APIRouter(prefix="/visit", tags=["visit-alias"])


@visit_alias_router.post("", summary="创建拜访(别名)", description="通过别名路径创建拜访记录。")
def create_visit_alias(
    body: VisitCreate,
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    service = VisitService()
    user_id = int(current_user["sub"])
    result = service.create_visit(body, user_id)
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@visit_alias_router.get("", summary="查询拜访列表(别名)", description="通过别名路径分页查询拜访记录。")
def list_visits_alias(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    hcp_id: Optional[int] = Query(None),
    visit_type: Optional[str] = Query(None),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[PaginatedResponse[VisitOut]]:
    service = VisitService()
    total, total_pages, rows = service.list_visits(
        page=page,
        page_size=page_size,
        hcp_id=hcp_id,
        visit_type=visit_type,
    )
    items = [VisitOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@visit_alias_router.get("/{visit_id}", summary="获取拜访详情(别名)", description="通过别名路径获取拜访记录。")
def get_visit_alias(
    visit_id: int,
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[VisitOut]:
    service = VisitService()
    row = service.get_visit(visit_id)
    return success(data=VisitOut(**row))
