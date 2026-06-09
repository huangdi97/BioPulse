"""日程路由：销售日程的CRUD接口。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from sales_assistant.app.services.schedule_service import ScheduleService
from shared.auth_scope import require_scope
from shared.base import ApiResponse, PaginatedResponse, success

router = APIRouter(prefix="/schedule")


class ScheduleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    event_type: Optional[str] = None
    start_time: str
    end_time: Optional[str] = None
    location: Optional[str] = None
    is_completed: Optional[int] = 0


class ScheduleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    is_completed: Optional[int] = None


class ScheduleOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    event_type: Optional[str] = None
    start_time: str
    end_time: Optional[str] = None
    location: Optional[str] = None
    is_completed: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("", summary="创建日程", description="创建销售日程", tags=["拜访"])
def create_schedule(
    body: ScheduleCreate,
    service: ScheduleService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    """创建schedule。"""
    user_id = int(current_user["sub"])
    new_id = service.create_schedule(body, user_id)
    return JSONResponse(content=success(data={"id": new_id}).model_dump(), status_code=201)


@router.get("", summary="日程列表", description="获取销售日程列表", tags=["拜访"])
def list_schedules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    event_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    service: ScheduleService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[PaginatedResponse[ScheduleOut]]:
    """获取schedules。"""
    total, total_pages, rows = service.list_schedules(
        page,
        page_size,
        event_type,
        start_date,
        end_date,
    )
    items = [ScheduleOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/{schedule_id}", summary="日程详情", description="获取指定日程详情", tags=["拜访"])
def get_schedule(
    schedule_id: int,
    service: ScheduleService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[ScheduleOut]:
    """获取schedule。"""
    row = service.get_schedule(schedule_id)
    return success(data=ScheduleOut(**row))


@router.patch("/{schedule_id}", summary="更新日程", description="更新指定日程", tags=["拜访"])
def update_schedule(
    schedule_id: int,
    body: ScheduleUpdate,
    service: ScheduleService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[ScheduleOut]:
    """更新schedule。"""
    row = service.update_schedule(schedule_id, body)
    return success(data=ScheduleOut(**row))


@router.delete("/{schedule_id}", summary="删除日程", description="删除指定日程", tags=["拜访"])
def delete_schedule(
    schedule_id: int,
    service: ScheduleService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """删除schedule。"""
    service.delete_schedule(schedule_id)
    return success(message="deleted")
