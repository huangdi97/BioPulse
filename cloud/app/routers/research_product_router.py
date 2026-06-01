from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status

from shared.auth import get_current_user
from shared.auth_scope import require_scope
from cloud.app.research_database import get_research_db

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
    db = get_research_db()
    try:
        conditions = []
        params = []
        if q:
            pattern = f"%{q}%"
            conditions.append("(name LIKE ? OR keywords LIKE ? OR brand LIKE ? OR model LIKE ?)")
            params.extend([pattern, pattern, pattern, pattern])
        if category:
            conditions.append("category = ?")
            params.append(category)
        where = ""
        if conditions:
            where = " WHERE " + " AND ".join(conditions)
        rows = db.execute(
            f"SELECT * FROM research_products{where} ORDER BY product_id DESC", params
        ).fetchall()
        return {"code": 0, "data": [dict(r) for r in rows], "message": "success"}
    finally:
        db.close()


@router.get("/{product_id}")
def get_product(
    product_id: int,
    current_user: dict = Depends(get_current_user),
):
    db = get_research_db()
    try:
        row = db.execute(
            "SELECT * FROM research_products WHERE product_id = ?", (product_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return {"code": 0, "data": dict(row), "message": "success"}
    finally:
        db.close()
