"""HCP 路由模块，定义 HCP 增删改查的 API 端点。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette import status

from assistant.app.services.hcp_service import HcpService
from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success

router = APIRouter(prefix="/hcp", tags=["hcp"])


class HcpCreate(BaseModel):
    """Request model for creating an HCP record."""

    name: str = Field(..., min_length=1, max_length=100)
    hospital: str
    department: Optional[str] = None
    title: Optional[str] = None
    specialty: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    wechat: Optional[str] = None
    email: Optional[str] = Field(None, max_length=100)
    level: Optional[str] = "C"


class HcpUpdate(BaseModel):
    """Request model for updating an HCP record."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    hospital: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    specialty: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    wechat: Optional[str] = None
    email: Optional[str] = Field(None, max_length=100)
    level: Optional[str] = None
    is_active: Optional[int] = None


class HcpOut(BaseModel):
    """Response model for an HCP record."""

    id: int
    name: str
    hospital: str
    department: Optional[str] = None
    title: Optional[str] = None
    specialty: Optional[str] = None
    phone: Optional[str] = None
    wechat: Optional[str] = None
    email: Optional[str] = None
    level: str
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("")
def create_hcp(
    body: HcpCreate,
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    """Create a new HCP record."""
    service = HcpService()
    user_id = int(current_user["sub"])
    result = service.create_hcp(body, user_id)
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("")
def list_hcps(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: Optional[str] = Query(None),
    hospital: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[HcpOut]]:
    """List HCP records with pagination and filtering."""
    service = HcpService()
    total, total_pages, rows = service.list_hcps(
        page=page,
        page_size=page_size,
        name=name,
        hospital=hospital,
        department=department,
        level=level,
    )
    items = [HcpOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/{hcp_id}")
def get_hcp(
    hcp_id: int,
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[HcpOut]:
    """Get a single HCP record by ID."""
    service = HcpService()
    row = service.get_hcp(hcp_id)
    return success(data=HcpOut(**dict(row)))


@router.patch("/{hcp_id}")
def update_hcp(
    hcp_id: int,
    body: HcpUpdate,
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[HcpOut]:
    """Update an HCP record."""
    service = HcpService()
    row = service.update_hcp(hcp_id, body)
    return success(data=HcpOut(**row))


@router.delete("/{hcp_id}")
def delete_hcp(
    hcp_id: int,
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """Soft-delete an HCP record by setting is_active to 0."""
    service = HcpService()
    service.delete_hcp(hcp_id)
    return success(message="deleted")


hcp_alias_router = APIRouter(tags=["hcp-alias"])


@hcp_alias_router.get("/hcps")
def list_hcps_alias(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: Optional[str] = Query(None),
    hospital: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[HcpOut]]:
    service = HcpService()
    total, total_pages, rows = service.list_hcps(
        page=page,
        page_size=page_size,
        name=name,
        hospital=hospital,
        department=department,
        level=level,
    )
    items = [HcpOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@hcp_alias_router.get("/hcps/{hcp_id}")
def get_hcp_alias(
    hcp_id: int,
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[HcpOut]:
    service = HcpService()
    row = service.get_hcp(hcp_id)
    return success(data=HcpOut(**row))


@hcp_alias_router.get("/hcp/list")
def hcp_list_alias(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: Optional[str] = Query(None),
    hospital: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[HcpOut]]:
    service = HcpService()
    total, total_pages, rows = service.list_hcps(
        page=page,
        page_size=page_size,
        name=name,
        hospital=hospital,
        department=department,
        level=level,
    )
    items = [HcpOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )
