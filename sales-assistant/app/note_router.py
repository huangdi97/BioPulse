"""笔记路由：拜访笔记的CRUD接口。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette import status

from sales_assistant.app.services.note_service import NoteService
from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success

router = APIRouter(tags=["notes"])


class NoteCreate(BaseModel):
    title: str
    content: str = Field(..., min_length=1, max_length=5000)
    participants: Optional[str] = None
    action_items: Optional[str] = None


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    participants: Optional[str] = None
    action_items: Optional[str] = None


class NoteOut(BaseModel):
    id: int
    schedule_id: int
    title: str
    content: Optional[str] = None
    participants: Optional[str] = None
    action_items: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("/schedule/{schedule_id}/notes", summary="创建笔记", description="创建拜访笔记")
def create_note(
    schedule_id: int,
    body: NoteCreate,
    service: NoteService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    """创建note。"""
    user_id = int(current_user["sub"])
    note_id = service.create_note(schedule_id, body, user_id)
    return JSONResponse(
        content=success(data={"id": note_id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/schedule/{schedule_id}/notes", summary="笔记列表", description="获取拜访笔记列表")
def list_notes(
    schedule_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: NoteService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[NoteOut]]:
    """获取notes。"""
    total, total_pages, rows = service.list_notes(schedule_id, page, page_size)
    items = [NoteOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/notes", summary="全部笔记", description="获取全部笔记")
def list_all_notes() -> list:
    """获取notes。"""
    return []


@router.get("/notes/{note_id}", summary="笔记详情", description="获取指定笔记详情")
def get_note(
    note_id: int,
    service: NoteService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[NoteOut]:
    """获取note。"""
    row = service.get_note(note_id)
    return success(data=NoteOut(**row))


@router.patch("/notes/{note_id}", summary="更新笔记", description="更新指定笔记")
def update_note(
    note_id: int,
    body: NoteUpdate,
    service: NoteService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[NoteOut]:
    """更新note。"""
    row = service.update_note(note_id, body)
    return success(data=NoteOut(**row))


@router.delete("/notes/{note_id}", summary="删除笔记", description="删除指定笔记")
def delete_note(
    note_id: int,
    service: NoteService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """删除note。"""
    service.delete_note(note_id)
    return success(message="deleted")
