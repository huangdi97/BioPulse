from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from starlette import status

from sales_assistant.app.repositories import (
    HcpRepository,
    ProductRepository,
    RelationRepository,
)
from sales_assistant.app.services.base import BaseService


class HcpService(BaseService):
    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_hcp(self, body, user_id: int) -> int:
        repo = HcpRepository(self.db)
        now = self._now()
        return repo.create(
            body.model_dump(),
            extra={"created_by": user_id, "created_at": now, "updated_at": now},
        )

    def list_hcps(
        self,
        page: int,
        page_size: int,
        name: Optional[str] = None,
        hospital: Optional[str] = None,
        department: Optional[str] = None,
    ) -> tuple:
        repo = HcpRepository(self.db)
        conditions, params = ["is_active = 1"], []
        if name:
            conditions.append("name LIKE ?")
            params.append(f"%{name}%")
        if hospital:
            conditions.append("hospital LIKE ?")
            params.append(f"%{hospital}%")
        if department:
            conditions.append("department LIKE ?")
            params.append(f"%{department}%")
        return repo.paginate(page, page_size, conditions, params)

    def get_hcp(self, hcp_id: int) -> dict:
        repo = HcpRepository(self.db)
        row = repo.get_by_id(hcp_id)
        if not row or not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
        return dict(row)

    def update_hcp(self, hcp_id: int, body) -> dict:
        repo = HcpRepository(self.db)
        row = repo.get_by_id(hcp_id)
        if not row or not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)
        updates["updated_at"] = self._now()
        repo.update(hcp_id, updates)
        return dict(repo.get_by_id(hcp_id))

    def delete_hcp(self, hcp_id: int) -> None:
        repo = HcpRepository(self.db)
        row = repo.get_by_id(hcp_id)
        if not row or not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
        repo.soft_delete(hcp_id)

    def get_graph(self, hcp_id: Optional[int], product_id: Optional[int]) -> dict:
        hcp_cond, hcp_params = ("AND h.id = ?", [hcp_id]) if hcp_id else ("", [])
        hcps = self.db.execute(
            f"SELECT id, name, COALESCE(tier,'C') AS tier, hospital FROM hcp WHERE is_active = 1 {hcp_cond}",
            hcp_params,
        ).fetchall()
        if hcp_id:
            prods = self.db.execute(
                "SELECT DISTINCT p.id, p.name, p.company FROM product p "
                "JOIN hcp_product_relation r ON p.id = r.product_id "
                "WHERE p.is_active = 1 AND r.is_active = 1 AND r.hcp_id = ?",
                (hcp_id,),
            ).fetchall()
        elif product_id:
            prods = self.db.execute(
                "SELECT id, name, company FROM product WHERE is_active = 1 AND id = ?",
                (product_id,),
            ).fetchall()
        else:
            prods = self.db.execute("SELECT id, name, company FROM product WHERE is_active = 1").fetchall()
        hcp_ids = [h["id"] for h in hcps]
        if hcp_ids:
            placeholders = ",".join("?" * len(hcp_ids))
            edges = self.db.execute(
                f"SELECT hcp_id, product_id, relation_type, strength FROM hcp_product_relation "
                f"WHERE is_active = 1 AND hcp_id IN ({placeholders})",
                hcp_ids,
            ).fetchall()
        else:
            edges = []
        nodes = [
            {
                "id": f"hcp:{h['id']}",
                "type": "hcp",
                "label": h["name"],
                "tier": h["tier"],
                "hospital": h["hospital"],
            }
            for h in hcps
        ]
        nodes += [
            {
                "id": f"product:{p['id']}",
                "type": "product",
                "label": p["name"],
                "company": p["company"],
            }
            for p in prods
        ]
        edge_list = [
            {
                "source": f"hcp:{e['hcp_id']}",
                "target": f"product:{e['product_id']}",
                "type": e["relation_type"],
                "strength": e["strength"],
            }
            for e in edges
        ]
        return {"nodes": nodes, "edges": edge_list}

    def create_product(self, body, user_id: int) -> int:
        repo = ProductRepository(self.db)
        now = self._now()
        return repo.create(
            body.model_dump(),
            extra={"created_by": user_id, "created_at": now, "updated_at": now},
        )

    def list_products(
        self,
        page: int,
        page_size: int,
        category: Optional[str] = None,
        company: Optional[str] = None,
    ) -> tuple:
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
            {
                "hcp_id": hcp_id,
                "product_id": body.product_id,
                "relation_type": body.relation_type,
                "strength": body.strength,
                "notes": body.notes,
            },
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
