"""拜访路由模块，定义拜访记录增删改查的 API 端点。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette import status

from assistant.app.services.visit_service import VisitService
from shared.auth import get_current_user
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


@router.post("")
def create_visit(
    body: VisitCreate,
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    """Create a new visit record."""
    service = VisitService()
    user_id = int(current_user["sub"])
    result = service.create_visit(body, user_id)
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("")
def list_visits(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    hcp_id: Optional[int] = Query(None),
    visit_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
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


@router.get("/{visit_id}")
def get_visit(
    visit_id: int,
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[VisitOut]:
    """Get a single visit record by ID."""
    service = VisitService()
    row = service.get_visit(visit_id)
    return success(data=VisitOut(**dict(row)))


@router.patch("/{visit_id}")
def update_visit(
    visit_id: int,
    body: VisitUpdate,
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[VisitOut]:
    """Update a visit record."""
    service = VisitService()
    row = service.update_visit(visit_id, body)
    return success(data=VisitOut(**row))


@router.delete("/{visit_id}")
def delete_visit(
    visit_id: int,
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """Delete a visit record."""
    service = VisitService()
    service.delete_visit(visit_id)
    return success(message="deleted")


visit_alias_router = APIRouter(prefix="/visit", tags=["visit-alias"])


@visit_alias_router.post("")
def create_visit_alias(
    body: VisitCreate,
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    service = VisitService()
    user_id = int(current_user["sub"])
    result = service.create_visit(body, user_id)
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@visit_alias_router.get("")
def list_visits_alias(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    hcp_id: Optional[int] = Query(None),
    visit_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
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


@visit_alias_router.get("/{visit_id}")
def get_visit_alias(
    visit_id: int,
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[VisitOut]:
    service = VisitService()
    row = service.get_visit(visit_id)
    return success(data=VisitOut(**row))
