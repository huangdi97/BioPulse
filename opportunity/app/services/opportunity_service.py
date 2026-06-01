from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from starlette import status

from opportunity.app.repositories import OpportunityRepository
from opportunity.app.services.base import BaseService


class OpportunityService(BaseService):
    def create_opportunity(self, body, user_id: int) -> int:
        repo = OpportunityRepository(self.db)
        now = datetime.now(timezone.utc).isoformat()
        extra = {"created_by": user_id, "created_at": now, "updated_at": now}
        return repo.create(body.model_dump(), extra)

    def list_opportunities(
        self,
        page: int,
        page_size: int,
        stage: Optional[str] = None,
        product: Optional[str] = None,
        hcp_name: Optional[str] = None,
    ) -> tuple:
        repo = OpportunityRepository(self.db)
        conditions = ["is_active = 1"]
        params: list = []

        if stage:
            conditions.append("stage = ?")
            params.append(stage)
        if product:
            conditions.append("product LIKE ?")
            params.append(f"%{product}%")
        if hcp_name:
            conditions.append("hcp_name LIKE ?")
            params.append(f"%{hcp_name}%")

        return repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params,
        )

    def get_opportunity(self, opportunity_id: int) -> dict:
        repo = OpportunityRepository(self.db)
        row = repo.get_by_id(opportunity_id)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
            )
        return dict(row)

    def update_opportunity(self, opportunity_id: int, body) -> dict:
        repo = OpportunityRepository(self.db)
        row = repo.get_by_id(opportunity_id)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
            )

        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)

        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(opportunity_id, updates)
        return dict(repo.get_by_id(opportunity_id))

    def delete_opportunity(self, opportunity_id: int) -> None:
        repo = OpportunityRepository(self.db)
        row = repo.get_by_id(opportunity_id)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
            )
        repo.soft_delete(opportunity_id)

    def list_all_active(self) -> list:
        repo = OpportunityRepository(self.db)
        return repo.list_all(conditions=["is_active = 1"])
