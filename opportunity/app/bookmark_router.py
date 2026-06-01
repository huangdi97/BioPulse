from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status

from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success
from opportunity.app.services.bookmark_service import BookmarkService

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


@router.post("")
def create_bookmark(
    body: BookmarkCreate,
    service: BookmarkService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    user_id = int(current_user["sub"])
    new_id = service.create_bookmark(body, user_id)
    return JSONResponse(
        content=success(data={"id": new_id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("")
def list_bookmarks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    entity_type: Optional[str] = Query(None),
    service: BookmarkService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[BookmarkOut]]:
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


@router.get("/check")
def check_bookmark(
    entity_type: str = Query(...),
    entity_id: int = Query(...),
    service: BookmarkService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[CheckBookmarkOut]:
    user_id = int(current_user["sub"])
    row = service.check_bookmark(entity_type, entity_id, user_id)
    if row:
        return success(data=CheckBookmarkOut(bookmarked=True, bookmark_id=row["id"]))
    return success(data=CheckBookmarkOut(bookmarked=False))


@router.delete("/{bookmark_id}")
def delete_bookmark(
    bookmark_id: int,
    service: BookmarkService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    user_id = int(current_user["sub"])
    service.delete_bookmark(bookmark_id, user_id)
    return success(message="deleted")
