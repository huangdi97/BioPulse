"""用户收藏 CRUD。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status

from opportunity.app.services.bookmark_service import BookmarkService
from shared.auth_scope import require_scope
from shared.base import ApiResponse, PaginatedResponse, success

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


class BookmarkCreate(BaseModel):
    entity_type: str
    entity_id: int
    title: Optional[str] = None
    notes: Optional[str] = None


class BookmarkOut(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    title: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[str] = None


class CheckBookmarkOut(BaseModel):
    bookmarked: bool
    bookmark_id: Optional[int] = None


@router.post("", summary="创建书签", description="创建新的用户书签")
def create_bookmark(
    body: BookmarkCreate,
    service: BookmarkService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    """创建书签。

    Args:
        body: 书签创建请求体。
        service: 书签服务实例。
        current_user: 当前登录用户信息。

    Returns:
        包含新书签 ID 的 JSON 响应。
    """
    user_id = int(current_user["sub"])
    new_id = service.create_bookmark(body, user_id)
    return JSONResponse(
        content=success(data={"id": new_id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("", summary="书签列表", description="分页获取书签列表，支持按实体类型筛选")
def list_bookmarks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    entity_type: Optional[str] = Query(None),
    service: BookmarkService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[PaginatedResponse[BookmarkOut]]:
    """获取书签列表（分页，支持按实体类型筛选）。

    Args:
        page: 页码，从 1 开始。
        page_size: 每页条数。
        entity_type: 按实体类型筛选。
        service: 书签服务实例。
        current_user: 当前登录用户信息。

    Returns:
        分页的书签列表响应。
    """
    user_id = int(current_user["sub"])
    total, total_pages, rows = service.list_bookmarks(
        page,
        page_size,
        user_id,
        entity_type,
    )
    items = [BookmarkOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/check", summary="检查书签", description="检查指定实体是否已被收藏")
def check_bookmark(
    entity_type: str = Query(...),
    entity_id: int = Query(...),
    service: BookmarkService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[CheckBookmarkOut]:
    """检查书签是否存在。

    Args:
        entity_type: 实体类型。
        entity_id: 实体 ID。
        service: 书签服务实例。
        current_user: 当前登录用户信息。

    Returns:
        书签状态（是否存在及书签 ID）。
    """
    user_id = int(current_user["sub"])
    row = service.check_bookmark(entity_type, entity_id, user_id)
    if row:
        return success(data=CheckBookmarkOut(bookmarked=True, bookmark_id=row["id"]))
    return success(data=CheckBookmarkOut(bookmarked=False))


@router.delete("/{bookmark_id}", summary="删除书签", description="删除指定的用户书签")
def delete_bookmark(
    bookmark_id: int,
    service: BookmarkService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """删除书签。

    Args:
        bookmark_id: 书签 ID。
        service: 书签服务实例。
        current_user: 当前登录用户信息。

    Returns:
        删除成功响应。
    """
    user_id = int(current_user["sub"])
    service.delete_bookmark(bookmark_id, user_id)
    return success(message="deleted")
