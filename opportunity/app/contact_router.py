"""联系记录 CRUD。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status

from opportunity.app.services.contact_service import ContactService
from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success

router = APIRouter(tags=["contacts"])


class ContactCreate(BaseModel):
    contact_type: Optional[str] = None
    summary: Optional[str] = None
    detail: Optional[str] = None
    contact_date: Optional[str] = None


class ContactUpdate(BaseModel):
    contact_type: Optional[str] = None
    summary: Optional[str] = None
    detail: Optional[str] = None
    contact_date: Optional[str] = None


class ContactOut(BaseModel):
    id: int
    opportunity_id: int
    contact_type: Optional[str] = None
    summary: Optional[str] = None
    detail: Optional[str] = None
    contact_date: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[str] = None


@router.post("/opportunities/{opportunity_id}/contacts")
def create_contact(
    opportunity_id: int,
    body: ContactCreate,
    service: ContactService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    """创建联系记录。

    Args:
        opportunity_id: 关联的商机 ID。
        body: 联系记录创建请求体。
        service: 联系记录服务实例。
        current_user: 当前登录用户信息。

    Returns:
        包含新联系记录 ID 的 JSON 响应。
    """
    user_id = int(current_user["sub"])
    new_id = service.create_contact(body, opportunity_id, user_id)
    return JSONResponse(
        content=success(data={"id": new_id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/opportunities/{opportunity_id}/contacts")
def list_contacts(
    opportunity_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ContactService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[ContactOut]]:
    """获取指定商机的联系记录列表（分页）。

    Args:
        opportunity_id: 商机 ID。
        page: 页码，从 1 开始。
        page_size: 每页条数。
        service: 联系记录服务实例。
        current_user: 当前登录用户信息。

    Returns:
        分页的联系记录列表响应。
    """
    total, total_pages, rows = service.list_contacts(
        opportunity_id,
        page,
        page_size,
    )
    items = [ContactOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/contacts/{contact_id}")
def get_contact(
    contact_id: int,
    service: ContactService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[ContactOut]:
    """获取联系记录详情。

    Args:
        contact_id: 联系记录 ID。
        service: 联系记录服务实例。
        current_user: 当前登录用户信息。

    Returns:
        联系记录详情响应。
    """
    row = service.get_contact(contact_id)
    return success(data=ContactOut(**row))


@router.patch("/contacts/{contact_id}")
def update_contact(
    contact_id: int,
    body: ContactUpdate,
    service: ContactService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[ContactOut]:
    """更新联系记录。

    Args:
        contact_id: 联系记录 ID。
        body: 联系记录更新请求体。
        service: 联系记录服务实例。
        current_user: 当前登录用户信息。

    Returns:
        更新后的联系记录信息响应。
    """
    updated = service.update_contact(contact_id, body)
    return success(data=ContactOut(**updated))


@router.delete("/contacts/{contact_id}")
def delete_contact(
    contact_id: int,
    service: ContactService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """删除联系记录。

    Args:
        contact_id: 联系记录 ID。
        service: 联系记录服务实例。
        current_user: 当前登录用户信息。

    Returns:
        删除成功响应。
    """
    service.delete_contact(contact_id)
    return success(message="deleted")
