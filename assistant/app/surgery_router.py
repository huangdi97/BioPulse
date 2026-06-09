"""跟台手术路由模块，定义手术提醒的增删改查与今日手术的 API 端点。"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status

from assistant.app.services.surgery_service import SurgeryService
from shared.auth_scope import require_scope
from shared.base import ApiResponse, PaginatedResponse, success

router = APIRouter(prefix="/surgery-reminders")


class SurgeryCreate(BaseModel):
    patient_name: str
    surgery_type: Optional[str] = None
    surgery_date: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    surgeon_name: Optional[str] = None
    pre_op_notes: Optional[str] = None
    post_op_notes: Optional[str] = None
    status: Optional[str] = None
    reminder_before: Optional[int] = None


class SurgeryUpdate(BaseModel):
    patient_name: Optional[str] = None
    surgery_type: Optional[str] = None
    surgery_date: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    surgeon_name: Optional[str] = None
    pre_op_notes: Optional[str] = None
    post_op_notes: Optional[str] = None
    status: Optional[str] = None
    reminder_before: Optional[int] = None


class SurgeryOut(BaseModel):
    id: int
    patient_name: str
    surgery_type: Optional[str] = None
    surgery_date: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    surgeon_name: Optional[str] = None
    pre_op_notes: Optional[str] = None
    post_op_notes: Optional[str] = None
    status: Optional[str] = None
    reminder_before: Optional[int] = None
    last_notified_at: Optional[str] = None
    notification_status: Optional[str] = None
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("", summary="创建手术提醒", description="创建新的手术提醒记录。", tags=["手术记录"])
def create_surgery(
    body: SurgeryCreate,
    service: SurgeryService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    """创建手术提醒记录。

    Args:
        body: 手术创建数据（患者姓名、手术类型、日期等）
        service: 手术服务
        current_user: 当前登录用户

    Returns:
        包含新创建手术记录的 JSON 响应
    """
    user_id = int(current_user["sub"])
    result = service.create(body, user_id)
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/today", summary="今日手术", description="获取今日的所有手术安排列表。", tags=["手术记录"])
def today_surgeries(
    service: SurgeryService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[List[SurgeryOut]]:
    """获取今日的所有手术安排。

    Args:
        service: 手术服务
        current_user: 当前登录用户

    Returns:
        今日手术列表
    """
    rows = service.today()
    return success(data=[SurgeryOut(**r) for r in rows])


@router.get("", summary="查询手术列表", description="分页查询手术提醒，支持多条件筛选。", tags=["手术记录"])
def list_surgeries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    patient_name: Optional[str] = Query(None),
    surgery_status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    service: SurgeryService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[PaginatedResponse[SurgeryOut]]:
    """分页查询手术提醒列表，支持按患者姓名、状态和日期范围筛选。

    Args:
        page: 页码（从1开始）
        page_size: 每页数量
        patient_name: 患者姓名（可选筛选）
        surgery_status: 手术状态（可选筛选）
        date_from: 开始日期（可选筛选）
        date_to: 结束日期（可选筛选）
        service: 手术服务
        current_user: 当前登录用户

    Returns:
        分页的手术提醒列表
    """
    total, total_pages, rows = service.list(
        page,
        page_size,
        patient_name,
        surgery_status,
        date_from,
        date_to,
    )
    return success(
        data=PaginatedResponse(
            items=[SurgeryOut(**dict(r)) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.post("/check-now", summary="立即检查提醒", description="立即触发检查并发送手术提醒通知。", tags=["手术记录"])
def check_reminders_now(
    service: SurgeryService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
):
    """立即触发检查手术提醒，发送到期待通知的患者。

    Args:
        service: 手术服务
        current_user: 当前登录用户

    Returns:
        检查结果
    """
    data = service.check_reminders_now()
    return success(data=data)


@router.get("/upcoming", summary="即将到来手术", description="分页查询即将到来的手术安排。", tags=["手术记录"])
def upcoming_surgeries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: SurgeryService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[PaginatedResponse[SurgeryOut]]:
    """分页查询即将到来的手术安排。

    Args:
        page: 页码（从1开始）
        page_size: 每页数量
        service: 手术服务
        current_user: 当前登录用户

    Returns:
        分页的即将到来手术列表
    """
    total, total_pages, rows = service.upcoming(page, page_size)
    return success(
        data=PaginatedResponse(
            items=[SurgeryOut(**dict(r)) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/{surgery_id}", summary="获取手术详情", description="根据ID获取手术提醒的详细信息。", tags=["手术记录"])
def get_surgery(
    surgery_id: int,
    service: SurgeryService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[SurgeryOut]:
    """获取指定手术提醒的详细信息。

    Args:
        surgery_id: 手术提醒 ID
        service: 手术服务
        current_user: 当前登录用户

    Returns:
        手术提醒详情
    """
    row = service.get(surgery_id)
    return success(data=SurgeryOut(**row))


@router.patch("/{surgery_id}", summary="更新手术提醒", description="更新指定手术提醒的部分字段信息。", tags=["手术记录"])
def update_surgery(
    surgery_id: int,
    body: SurgeryUpdate,
    service: SurgeryService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[SurgeryOut]:
    """更新指定手术提醒的部分字段。

    Args:
        surgery_id: 手术提醒 ID
        body: 需要更新的字段数据
        service: 手术服务
        current_user: 当前登录用户

    Returns:
        更新后的手术提醒
    """
    updated = service.update(surgery_id, body)
    return success(data=SurgeryOut(**updated))


@router.delete("/{surgery_id}", summary="删除手术提醒", description="删除指定的手术提醒记录。", tags=["手术记录"])
def delete_surgery(
    surgery_id: int,
    service: SurgeryService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """删除指定手术提醒记录。

    Args:
        surgery_id: 手术提醒 ID
        service: 手术服务
        current_user: 当前登录用户

    Returns:
        成功删除的消息
    """
    service.delete(surgery_id)
    return success(message="deleted")
