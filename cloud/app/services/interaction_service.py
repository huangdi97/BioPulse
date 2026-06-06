"""客户互动服务，负责客户拜访与互动记录的管理。"""

from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import CustomerInteractionsRepository, CustomersRepository
from cloud.app.services.base import BaseService
from shared.base import validate_columns
from shared.columns import TABLE_CUSTOMER_INTERACTIONS_COLS


class InteractionService(BaseService):
    """客户互动服务，提供客户互动的创建、查询与列表功能。"""

    def create_interaction(
        self,
        customer_id: int,
        type_: str,
        summary: str,
        outcome: str,
        conducted_by: Optional[int],
        conducted_at: Optional[str],
        user_id: int,
    ) -> dict:
        customers_repo = CustomersRepository(self.db)
        interactions_repo = CustomerInteractionsRepository(self.db)
        if not customers_repo.exists(customer_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Customer not found")
        data = {
            "customer_id": customer_id,
            "type": type_,
            "summary": summary,
            "outcome": outcome,
            "conducted_by": conducted_by or user_id,
            "conducted_at": conducted_at,
        }
        row_id = interactions_repo.create(data)
        return interactions_repo.get_by_id(row_id)

    def list_customer_interactions(self, customer_id: int) -> list:
        return CustomerInteractionsRepository(self.db).list_by_customer_id(customer_id)

    def list_interactions(
        self,
        type_: str = None,
        conducted_by: int = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        interactions_repo = CustomerInteractionsRepository(self.db)
        total, total_pages, items = interactions_repo.list_filtered(type_=type_, conducted_by=conducted_by, page=page, page_size=page_size)
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def update_interaction(self, interaction_id: int, updates: dict) -> dict:
        interactions_repo = CustomerInteractionsRepository(self.db)
        row = interactions_repo.get_by_id(interaction_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Interaction not found")
        if updates:
            validate_columns(updates, "customer_interactions", TABLE_CUSTOMER_INTERACTIONS_COLS)
            interactions_repo.update(interaction_id, updates)
        return interactions_repo.get_by_id(interaction_id)

    def delete_interaction(self, interaction_id: int) -> None:
        interactions_repo = CustomerInteractionsRepository(self.db)
        if not interactions_repo.get_by_id(interaction_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Interaction not found")
        interactions_repo.delete(interaction_id)
