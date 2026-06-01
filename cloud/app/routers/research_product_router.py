from fastapi import APIRouter, Depends, Query

from cloud.app.services.research_product_service import ResearchProductService
from shared.auth import get_current_user
from shared.auth_scope import require_scope

router = APIRouter(
    prefix="/api/research/products",
    tags=["科研线"],
    dependencies=[Depends(require_scope("research"))],
)


@router.get("/search")
def search_products(
    q: str = Query("", description="Search keyword"),
    category: str = Query("", description="Filter by category"),
    current_user: dict = Depends(get_current_user),
):
    service = ResearchProductService()
    results = service.search(q=q, category=category)
    return {"code": 0, "data": results, "message": "success"}


@router.get("/{product_id}")
def get_product(
    product_id: int,
    current_user: dict = Depends(get_current_user),
):
    service = ResearchProductService()
    product = service.get_by_id(product_id)
    return {"code": 0, "data": product, "message": "success"}
