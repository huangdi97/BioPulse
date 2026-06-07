"""HCP 产品/关系辅助 mixin。"""

from typing import Optional

from fastapi import HTTPException
from starlette import status

from sales_assistant.app.repositories import HcpRepository, ProductRepository, RelationRepository


class HcpStatsMixin:
    def create_product(self, body, user_id: int) -> int:
        repo = ProductRepository(self.db)
        now = self._now()
        return repo.create(body.model_dump(), extra={"created_by": user_id, "created_at": now, "updated_at": now})

    def list_products(self, page: int, page_size: int, category: Optional[str] = None, company: Optional[str] = None) -> tuple:
        repo = ProductRepository(self.db)
        conditions, params = ["is_active = 1"], []
        if category:
            conditions.append("category LIKE ?")
            params.append(f"%{category}%")
        if company:
            conditions.append("company LIKE ?")
            params.append(f"%{company}%")
        return repo.paginate(page, page_size, conditions, params)

    def get_product(self, product_id: int) -> dict:
        repo = ProductRepository(self.db)
        row = repo.get_by_id(product_id)
        if not row or not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return dict(row)

    def update_product(self, product_id: int, body) -> dict:
        repo = ProductRepository(self.db)
        row = repo.get_by_id(product_id)
        if not row or not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)
        updates["updated_at"] = self._now()
        repo.update(product_id, updates)
        return dict(repo.get_by_id(product_id))

    def delete_product(self, product_id: int) -> None:
        repo = ProductRepository(self.db)
        row = repo.get_by_id(product_id)
        if not row or not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        repo.soft_delete(product_id)

    def create_relation(self, hcp_id: int, body, user_id: int) -> int:
        hcp_repo = HcpRepository(self.db)
        product_repo = ProductRepository(self.db)
        relation_repo = RelationRepository(self.db)
        hcp_row = hcp_repo.get_by_id(hcp_id)
        if not hcp_row or not hcp_row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
        prod_row = product_repo.get_by_id(body.product_id)
        if not prod_row or not prod_row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        now = self._now()
        return relation_repo.create(
            {"hcp_id": hcp_id, "product_id": body.product_id, "relation_type": body.relation_type, "strength": body.strength, "notes": body.notes},
            extra={"created_by": user_id, "created_at": now, "updated_at": now},
        )

    def list_relations(self, hcp_id: int) -> list:
        hcp_repo = HcpRepository(self.db)
        hcp_row = hcp_repo.get_by_id(hcp_id)
        if not hcp_row or not hcp_row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
        rows = self.db.execute(
            "SELECT r.id, r.hcp_id, r.product_id, r.relation_type, r.strength, "
            "r.notes, r.is_active, p.name AS product_name "
            "FROM hcp_product_relation r JOIN product p ON r.product_id = p.id "
            "WHERE r.hcp_id = ? AND r.is_active = 1 AND p.is_active = 1",
            (hcp_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_relation(self, relation_id: int) -> None:
        repo = RelationRepository(self.db)
        row = repo.get_by_id(relation_id)
        if not row or not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relation not found")
        repo.soft_delete(relation_id)
