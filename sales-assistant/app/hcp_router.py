from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette import status

from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success
from sales_assistant.app.services.hcp_service import HcpService

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


@router.post("/hcp")
def create_hcp(
    body: HcpCreate,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    user_id = int(current_user["sub"])
    hcp_id = service.create_hcp(body, user_id)
    return JSONResponse(
        content=success(data={"id": hcp_id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/hcp")
def list_hcp(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: Optional[str] = Query(None),
    hospital: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[HcpOut]]:
    total, total_pages, rows = service.list_hcps(
        page, page_size, name, hospital, department
    )
    return success(
        data=PaginatedResponse(
            items=[HcpOut(**dict(r)) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/hcp/graph")
def get_graph(
    hcp_id: Optional[int] = Query(None),
    product_id: Optional[int] = Query(None),
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    data = service.get_graph(hcp_id, product_id)
    return success(data=data)


@router.get("/hcp/{hcp_id}")
def get_hcp(
    hcp_id: int,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[HcpOut]:
    row = service.get_hcp(hcp_id)
    return success(data=HcpOut(**row))


@router.patch("/hcp/{hcp_id}")
def update_hcp(
    hcp_id: int,
    body: HcpUpdate,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[HcpOut]:
    row = service.update_hcp(hcp_id, body)
    return success(data=HcpOut(**row))


@router.delete("/hcp/{hcp_id}")
def delete_hcp(
    hcp_id: int,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    service.delete_hcp(hcp_id)
    return success(message="deleted")


@router.post("/products")
def create_product(
    body: ProductCreate,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    user_id = int(current_user["sub"])
    product_id = service.create_product(body, user_id)
    return JSONResponse(
        content=success(data={"id": product_id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/products")
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[ProductOut]]:
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


@router.get("/products/{product_id}")
def get_product(
    product_id: int,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[ProductOut]:
    row = service.get_product(product_id)
    return success(data=ProductOut(**row))


@router.patch("/products/{product_id}")
def update_product(
    product_id: int,
    body: ProductUpdate,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[ProductOut]:
    row = service.update_product(product_id, body)
    return success(data=ProductOut(**row))


@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    service.delete_product(product_id)
    return success(message="deleted")


@router.post("/hcp/{hcp_id}/products")
def create_relation(
    hcp_id: int,
    body: RelationCreate,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    user_id = int(current_user["sub"])
    relation_id = service.create_relation(hcp_id, body, user_id)
    return JSONResponse(
        content=success(data={"id": relation_id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/hcp/{hcp_id}/products")
def list_relations(
    hcp_id: int,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[List[RelationOut]]:
    rows = service.list_relations(hcp_id)
    return success(data=[RelationOut(**r) for r in rows])


@router.delete("/hcp/relations/{relation_id}")
def delete_relation(
    relation_id: int,
    service: HcpService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    service.delete_relation(relation_id)
    return success(message="deleted")
