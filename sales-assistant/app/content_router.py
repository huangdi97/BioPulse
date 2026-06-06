"""内容路由：销售内容库的CRUD接口。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status

from sales_assistant.app.services.content_service import ContentService
from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success

router = APIRouter(prefix="/contents", tags=["contents"])


class ContentCreate(BaseModel):
    title: str
    content_type: Optional[str] = "product_material"
    category: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    summary: Optional[str] = None
    file_reference: Optional[str] = None


class ContentUpdate(BaseModel):
    title: Optional[str] = None
    content_type: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    summary: Optional[str] = None
    file_reference: Optional[str] = None
    is_active: Optional[int] = None


class ContentOut(BaseModel):
    id: int
    title: str
    content_type: str
    category: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    summary: Optional[str] = None
    file_reference: Optional[str] = None
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("", summary="创建内容", description="创建销售内容")
def create_content(
    body: ContentCreate,
    service: ContentService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    """创建content。"""
    user_id = int(current_user["sub"])
    row_id = service.create_content(body, user_id)
    return JSONResponse(
        content=success(data={"id": row_id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("", summary="内容列表", description="获取销售内容列表")
def list_contents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    content_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    service: ContentService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[ContentOut]]:
    """获取contents。"""
    total, total_pages, rows = service.list_contents(
        page,
        page_size,
        content_type,
        category,
        tag,
        q,
    )
    items = [ContentOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/types", summary="类型列表", description="获取内容类型列表")
def list_content_types(
    service: ContentService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[list]:
    """获取content types。"""
    return success(data=service.list_content_types())


@router.get("/{content_id}", summary="内容详情", description="获取指定销售内容详情")
def get_content(
    content_id: int,
    service: ContentService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[ContentOut]:
    """获取content。"""
    row = service.get_content(content_id)
    return success(data=ContentOut(**row))


@router.patch("/{content_id}", summary="更新内容", description="更新指定销售内容")
def update_content(
    content_id: int,
    body: ContentUpdate,
    service: ContentService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[ContentOut]:
    """更新content。"""
    row = service.update_content(content_id, body)
    return success(data=ContentOut(**row))


@router.delete("/{content_id}", summary="删除内容", description="删除指定销售内容")
def delete_content(
    content_id: int,
    service: ContentService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """删除content。"""
    service.delete_content(content_id)
    return success(message="deleted")


content_root_router = APIRouter()


@content_root_router.get("/content", summary="内容根路径", description="获取内容根路径")
def get_content_root() -> list:
    """获取content。"""
    return []
