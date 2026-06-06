"""招投标信息 CRUD。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status

from opportunity.app.services.bidding_service import BiddingService
from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success

router = APIRouter(prefix="/bidding", tags=["bidding"])


class BiddingCreate(BaseModel):
    title: str
    hospital: Optional[str] = None
    department: Optional[str] = None
    product_category: Optional[str] = None
    budget: Optional[float] = None
    publish_date: Optional[str] = None
    deadline: Optional[str] = None
    source_url: Optional[str] = None
    summary: Optional[str] = None
    notes: Optional[str] = None


class BiddingUpdate(BaseModel):
    title: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    product_category: Optional[str] = None
    budget: Optional[float] = None
    publish_date: Optional[str] = None
    deadline: Optional[str] = None
    source_url: Optional[str] = None
    summary: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    analysis: Optional[str] = None
    is_active: Optional[int] = None


class BiddingOut(BaseModel):
    id: int
    title: str
    hospital: Optional[str] = None
    department: Optional[str] = None
    product_category: Optional[str] = None
    budget: Optional[float] = None
    publish_date: Optional[str] = None
    deadline: Optional[str] = None
    status: str = "new"
    source_url: Optional[str] = None
    summary: Optional[str] = None
    analysis: Optional[str] = None
    notes: Optional[str] = None
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("")
def create_bidding(
    body: BiddingCreate,
    service: BiddingService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    """创建招标记录。

    Args:
        body: 招标创建请求体。
        service: 招标服务实例。
        current_user: 当前登录用户信息。

    Returns:
        包含新招标 ID 的 JSON 响应。
    """
    user_id = int(current_user["sub"])
    new_id = service.create_bidding(body, user_id)
    return JSONResponse(
        content=success(data={"id": new_id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("")
def list_bidding(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_val: Optional[str] = Query(None, alias="status"),
    hospital: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    product_category: Optional[str] = Query(None),
    service: BiddingService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[BiddingOut]]:
    """获取招标列表（分页，支持筛选）。

    Args:
        page: 页码，从 1 开始。
        page_size: 每页条数。
        status_val: 按状态筛选。
        hospital: 按医院筛选。
        department: 按科室筛选。
        product_category: 按产品类别筛选。
        service: 招标服务实例。
        current_user: 当前登录用户信息。

    Returns:
        分页的招标列表响应。
    """
    total, total_pages, rows = service.list_bidding(
        page,
        page_size,
        status_val=status_val,
        hospital=hospital,
        department=department,
        product_category=product_category,
    )
    items = [BiddingOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/{bidding_id}")
def get_bidding(
    bidding_id: int,
    service: BiddingService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[BiddingOut]:
    """获取招标详情。

    Args:
        bidding_id: 招标 ID。
        service: 招标服务实例。
        current_user: 当前登录用户信息。

    Returns:
        招标详情响应。
    """
    row = service.get_bidding(bidding_id)
    return success(data=BiddingOut(**row))


@router.patch("/{bidding_id}")
def update_bidding(
    bidding_id: int,
    body: BiddingUpdate,
    service: BiddingService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[BiddingOut]:
    """更新招标信息。

    Args:
        bidding_id: 招标 ID。
        body: 招标更新请求体。
        service: 招标服务实例。
        current_user: 当前登录用户信息。

    Returns:
        更新后的招标信息响应。
    """
    updated = service.update_bidding(bidding_id, body)
    return success(data=BiddingOut(**updated))


@router.delete("/{bidding_id}")
def delete_bidding(
    bidding_id: int,
    service: BiddingService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """删除招标记录。

    Args:
        bidding_id: 招标 ID。
        service: 招标服务实例。
        current_user: 当前登录用户信息。

    Returns:
        删除成功响应。
    """
    service.delete_bidding(bidding_id)
    return success(message="deleted")
