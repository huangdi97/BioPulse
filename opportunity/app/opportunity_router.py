"""商机线索 CRUD。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette import status

from opportunity.app.services.opportunity_service import OpportunityService
from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


class OpportunityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    hcp_name: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    product: Optional[str] = None
    estimated_value: Optional[float] = None
    stage: Optional[str] = "lead"
    probability: Optional[int] = 10
    expected_close_date: Optional[str] = None
    notes: Optional[str] = None


class OpportunityUpdate(BaseModel):
    name: Optional[str] = None
    hcp_name: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    product: Optional[str] = None
    estimated_value: Optional[float] = None
    stage: Optional[str] = None
    probability: Optional[int] = None
    expected_close_date: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[int] = None


class OpportunityOut(BaseModel):
    id: int
    name: str
    hcp_name: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    product: Optional[str] = None
    estimated_value: Optional[float] = None
    stage: str
    probability: int
    expected_close_date: Optional[str] = None
    notes: Optional[str] = None
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("", summary="创建商机", description="创建新的商机线索")
def create_opportunity(
    body: OpportunityCreate,
    service: OpportunityService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    """创建商机。

    Args:
        body: 商机创建请求体。
        service: 商机服务实例。
        current_user: 当前登录用户信息。

    Returns:
        包含新商机 ID 的 JSON 响应。
    """
    user_id = int(current_user["sub"])
    id = service.create_opportunity(body, user_id)
    return JSONResponse(
        content=success(data={"id": id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("", summary="商机列表", description="分页查询商机列表，支持按阶段、产品等筛选")
def list_opportunities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    stage: Optional[str] = Query(None),
    product: Optional[str] = Query(None),
    hcp_name: Optional[str] = Query(None),
    service: OpportunityService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[OpportunityOut]]:
    """获取商机列表（分页，支持筛选）。

    Args:
        page: 页码，从 1 开始。
        page_size: 每页条数。
        stage: 按阶段筛选。
        product: 按产品筛选。
        hcp_name: 按医生姓名筛选。
        service: 商机服务实例。
        current_user: 当前登录用户信息。

    Returns:
        分页的商机列表响应。
    """
    total, total_pages, rows = service.list_opportunities(
        page=page,
        page_size=page_size,
        stage=stage,
        product=product,
        hcp_name=hcp_name,
    )
    items = [OpportunityOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/{opportunity_id}", summary="商机详情", description="获取指定商机的详细信息")
def get_opportunity(
    opportunity_id: int,
    service: OpportunityService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[OpportunityOut]:
    """获取商机详情。

    Args:
        opportunity_id: 商机 ID。
        service: 商机服务实例。
        current_user: 当前登录用户信息。

    Returns:
        商机详情响应。
    """
    row = service.get_opportunity(opportunity_id)
    return success(data=OpportunityOut(**row))


@router.patch("/{opportunity_id}", summary="更新商机", description="更新指定商机的信息")
def update_opportunity(
    opportunity_id: int,
    body: OpportunityUpdate,
    service: OpportunityService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[OpportunityOut]:
    """更新商机信息。

    Args:
        opportunity_id: 商机 ID。
        body: 商机更新请求体。
        service: 商机服务实例。
        current_user: 当前登录用户信息。

    Returns:
        更新后的商机信息响应。
    """
    updated = service.update_opportunity(opportunity_id, body)
    return success(data=OpportunityOut(**updated))


@router.delete("/{opportunity_id}", summary="删除商机", description="删除指定的商机记录")
def delete_opportunity(
    opportunity_id: int,
    service: OpportunityService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """删除商机。

    Args:
        opportunity_id: 商机 ID。
        service: 商机服务实例。
        current_user: 当前登录用户信息。

    Returns:
        删除成功响应。
    """
    service.delete_opportunity(opportunity_id)
    return success(message="deleted")
