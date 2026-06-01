from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from starlette import status
from shared.auth import get_current_user
from cloud.app.dependencies import get_db
from cloud.app.repositories.product_repository import ProductRepository

router = APIRouter(prefix="/api/products", tags=["products"])


class ProductCreate(BaseModel):
    """Request body for creating a new product."""
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
    db=Depends(get_db),
):
    """Search products by name, keyword, brand, or model, optionally filtered by category."""
    repo = ProductRepository(db)
    results = repo.search(q=q, category=category)
    return {"code": 0, "data": results, "message": "success"}


@router.get("/{product_id}")
def get_product(product_id: int,
                current_user: dict = Depends(get_current_user),
                db=Depends(get_db)):
    """Get a single product by ID."""
    repo = ProductRepository(db)
    product = repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return {"code": 0, "data": product, "message": "success"}


@router.post("", status_code=201)
def create_product(body: ProductCreate,
                   current_user: dict = Depends(get_current_user),
                   db=Depends(get_db)):
    """Create a new product entry."""
    repo = ProductRepository(db)
    product_id = repo.create(
        name=body.name, category=body.category, brand=body.brand,
        model=body.model, spec=body.spec, unit_price=body.unit_price,
        keywords=body.keywords, tech_params=body.tech_params,
        cert_status=body.cert_status,
    )
    product = repo.get_by_id(product_id)
    return {"code": 0, "data": product, "message": "success"}
