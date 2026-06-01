import json
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import CustomersRepository
from cloud.app.services.base import BaseService
from shared.base import validate_columns
from shared.columns import TABLE_CUSTOMERS_COLS


class CustomerService(BaseService):
    def _get_customer_or_404(self, repo: CustomersRepository, customer_id: int) -> dict:
        row = repo.get_by_id(customer_id)
        if not row or row.get("status") != "active":
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Customer not found")
        return row

    def create_customer(
        self,
        name: str,
        title: str,
        hospital: str,
        department: str,
        specialty: str,
        phone: str,
        email: str,
        tags: List[str],
        user_id: int,
    ) -> dict:
        repo = CustomersRepository(self.db)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        customer_id = repo.create(
            {
                "name": name,
                "title": title,
                "hospital": hospital,
                "department": department,
                "specialty": specialty,
                "phone": phone,
                "email": email,
                "tags": json.dumps(tags),
                "created_by": user_id,
                "created_at": now,
                "updated_at": now,
            }
        )
        return repo.get_by_id(customer_id)

    def list_customers(
        self,
        name: Optional[str] = None,
        hospital: Optional[str] = None,
        department: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        repo = CustomersRepository(self.db)
        conditions = ["1=1"]
        params: list = []
        if name:
            conditions.append("name LIKE ?")
            params.append(f"%{name}%")
        if hospital:
            conditions.append("hospital LIKE ?")
            params.append(f"%{hospital}%")
        if department:
            conditions.append("department LIKE ?")
            params.append(f"%{department}%")
        if status:
            conditions.append("status = ?")
            params.append(status)
        total, total_pages, rows = repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params,
            order_by="updated_at DESC",
        )
        return {
            "items": rows,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_customer(self, customer_id: int) -> dict:
        repo = CustomersRepository(self.db)
        return self._get_customer_or_404(repo, customer_id)

    def update_customer(
        self,
        customer_id: int,
        name: Optional[str] = None,
        title: Optional[str] = None,
        hospital: Optional[str] = None,
        department: Optional[str] = None,
        specialty: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> dict:
        repo = CustomersRepository(self.db)
        self._get_customer_or_404(repo, customer_id)
        field_map = {
            "name": name,
            "title": title,
            "hospital": hospital,
            "department": department,
            "specialty": specialty,
            "phone": phone,
            "email": email,
            "status": status,
        }
        updates = {k: v for k, v in field_map.items() if v is not None}
        if tags is not None:
            updates["tags"] = json.dumps(tags)
        if updates:
            updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            validate_columns(updates, "customers", TABLE_CUSTOMERS_COLS)
            repo.update(customer_id, updates)
        return self._get_customer_or_404(repo, customer_id)

    def delete_customer(self, customer_id: int) -> None:
        repo = CustomersRepository(self.db)
        self._get_customer_or_404(repo, customer_id)
        repo.update(customer_id, {"status": "inactive"})
