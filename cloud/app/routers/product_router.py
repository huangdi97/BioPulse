from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from cloud.app.services.product_service import ProductService
from shared.auth import get_current_user

router = APIRouter(prefix="/api/products", tags=["products"])


class ProductCreate(BaseModel):
    name: str
    category: str = ""
    brand: str = ""
    model: str = ""
    spec: str = ""
    unit_price: float = 0.0
    keywords: list[str] = []
    tech_params: dict = {}
    cert_status: str = ""


@router.get("/search")
def search_products(
    q: str = Query("", description="Search keyword"),
    category: str = Query("", description="Category filter"),
    current_user: dict = Depends(get_current_user),
    service: ProductService = Depends(),
):
    results = service.search(q=q, category=category)
    return {"code": 0, "data": results, "message": "success"}


@router.get("/{product_id}")
def get_product(
    product_id: int,
    current_user: dict = Depends(get_current_user),
    service: ProductService = Depends(),
):
    product = service.get_by_id(product_id)
    return {"code": 0, "data": product, "message": "success"}


@router.post("", status_code=201)
def create_product(
    body: ProductCreate,
    current_user: dict = Depends(get_current_user),
    service: ProductService = Depends(),
):
    product = service.create(
        name=body.name,
        category=body.category,
        brand=body.brand,
        model=body.model,
        spec=body.spec,
        unit_price=body.unit_price,
        keywords=body.keywords,
        tech_params=body.tech_params,
        cert_status=body.cert_status,
    )
    return {"code": 0, "data": product, "message": "success"}
