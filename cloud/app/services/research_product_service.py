from fastapi import HTTPException
from starlette import status

from cloud.app.research_database import get_research_db


class ResearchProductService:
    def search(self, q: str = "", category: str = "") -> list:
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
                f"SELECT * FROM research_products{where} ORDER BY product_id DESC",
                params,
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            db.close()

    def get_by_id(self, product_id: int) -> dict:
        db = get_research_db()
        try:
            row = db.execute("SELECT * FROM research_products WHERE product_id = ?", (product_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
            return dict(row)
        finally:
            db.close()
