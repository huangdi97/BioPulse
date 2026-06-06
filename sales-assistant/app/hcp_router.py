"""HCP路由：HCP、产品及关联关系管理的API端点。"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette import status

from sales_assistant.app.services.hcp_service import HcpService
from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success

router = APIRouter(tags=["hcp", "products"])


class HcpCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    hospital: Optional[str] = None
    department: Optional[str] = None
    specialty: Optional[str] = None
    tier: Optional[str] = "C"
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    wechat: Optional[str] = None


class HcpUpdate(BaseModel):
    name: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    specialty: Optional[str] = None
    tier: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    wechat: Optional[str] = None


class HcpOut(BaseModel):
    id: int
    name: str
    hospital: Optional[str] = None
    department: Optional[str] = None
    specialty: Optional[str] = None
    tier: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    wechat: Optional[str] = None
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = None
    specification: Optional[str] = None
    company: Optional[str] = Field(None, max_length=100)


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    specification: Optional[str] = None
    company: Optional[str] = None


class ProductOut(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    specification: Optional[str] = None
    company: Optional[str] = None
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RelationCreate(BaseModel):
    product_id: int
    relation_type: str
    strength: Optional[int] = 3
    notes: Optional[str] = None


class RelationOut(BaseModel):
    id: int
    hcp_id: int
    product_id: int
    relation_type: str
    strength: Optional[int] = None
    notes: Optional[str] = None
    is_active: int
    product_name: Optional[str] = None


@router.post("/hcp", summary="创建HCP", description="创建HCP信息")
def create_hcp(
    body: HcpCreate,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    """创建hcp。"""
    user_id = int(current_user["sub"])
    hcp_id = service.create_hcp(body, user_id)
    return JSONResponse(
        content=success(data={"id": hcp_id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/hcp", summary="HCP列表", description="获取HCP列表")
def list_hcp(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: Optional[str] = Query(None),
    hospital: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[HcpOut]]:
    """获取hcp。"""
    total, total_pages, rows = service.list_hcps(page, page_size, name, hospital, department)
    return success(
        data=PaginatedResponse(
            items=[HcpOut(**dict(r)) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/hcp/graph", summary="关系图谱", description="获取HCP关系图谱")
def get_graph(
    hcp_id: Optional[int] = Query(None),
    product_id: Optional[int] = Query(None),
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """获取graph。"""
    data = service.get_graph(hcp_id, product_id)
    return success(data=data)


@router.get("/hcp/{hcp_id}", summary="HCP详情", description="获取指定HCP详情")
def get_hcp(
    hcp_id: int,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[HcpOut]:
    """获取hcp。"""
    row = service.get_hcp(hcp_id)
    return success(data=HcpOut(**row))


@router.patch("/hcp/{hcp_id}", summary="更新HCP", description="更新指定HCP信息")
def update_hcp(
    hcp_id: int,
    body: HcpUpdate,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[HcpOut]:
    """更新hcp。"""
    row = service.update_hcp(hcp_id, body)
    return success(data=HcpOut(**row))


@router.delete("/hcp/{hcp_id}", summary="删除HCP", description="删除指定HCP")
def delete_hcp(
    hcp_id: int,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """删除hcp。"""
    service.delete_hcp(hcp_id)
    return success(message="deleted")


@router.post("/products", summary="创建产品", description="创建产品信息")
def create_product(
    body: ProductCreate,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    """创建product。"""
    user_id = int(current_user["sub"])
    product_id = service.create_product(body, user_id)
    return JSONResponse(
        content=success(data={"id": product_id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/products", summary="产品列表", description="获取产品列表")
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[ProductOut]]:
    """获取products。"""
    total, total_pages, rows = service.list_products(page, page_size, category, company)
    return success(
        data=PaginatedResponse(
            items=[ProductOut(**dict(r)) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/products/{product_id}", summary="产品详情", description="获取指定产品详情")
def get_product(
    product_id: int,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[ProductOut]:
    """获取product。"""
    row = service.get_product(product_id)
    return success(data=ProductOut(**row))


@router.patch("/products/{product_id}", summary="更新产品", description="更新指定产品信息")
def update_product(
    product_id: int,
    body: ProductUpdate,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[ProductOut]:
    """更新product。"""
    row = service.update_product(product_id, body)
    return success(data=ProductOut(**row))


@router.delete("/products/{product_id}", summary="删除产品", description="删除指定产品")
def delete_product(
    product_id: int,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """删除product。"""
    service.delete_product(product_id)
    return success(message="deleted")


@router.post("/hcp/{hcp_id}/products", summary="创建关联", description="创建HCP与产品关联")
def create_relation(
    hcp_id: int,
    body: RelationCreate,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    """创建relation。"""
    user_id = int(current_user["sub"])
    relation_id = service.create_relation(hcp_id, body, user_id)
    return JSONResponse(
        content=success(data={"id": relation_id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/hcp/{hcp_id}/products", summary="关联列表", description="获取HCP产品关联列表")
def list_relations(
    hcp_id: int,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[List[RelationOut]]:
    """获取relations。"""
    rows = service.list_relations(hcp_id)
    return success(data=[RelationOut(**r) for r in rows])


@router.delete("/hcp/relations/{relation_id}", summary="删除关联", description="删除指定HCP产品关联")
def delete_relation(
    relation_id: int,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """删除relation。"""
    service.delete_relation(relation_id)
    return success(message="deleted")
