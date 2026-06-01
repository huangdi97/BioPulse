from typing import List, Optional

from fastapi import HTTPException
from starlette import status

from assistant.app.repositories import HcpRepository, VisitRecordRepository
from assistant.app.services.base import BaseService


class VisitService(BaseService):
    def _check_hcp_exists(self, hcp_id: int) -> None:
        repo = HcpRepository(self.db)
        row = repo.get_by_id(hcp_id)
        if not row or row["is_active"] != 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")

    def create_visit(self, body, user_id: int) -> dict:
        self._check_hcp_exists(body.hcp_id)
        repo = VisitRecordRepository(self.db)
        row_id = repo.create(
            body.model_dump(),
            extra={"created_by": user_id},
        )
        return {"id": row_id}

    def list_visits(
        self,
        page: int,
        page_size: int,
        hcp_id: Optional[int] = None,
        visit_type: Optional[str] = None,
    ) -> tuple:
        repo = VisitRecordRepository(self.db)
        conditions: List[str] = []
        params: list = []

        if hcp_id is not None:
            conditions.append("hcp_id = ?")
            params.append(hcp_id)
        if visit_type:
            conditions.append("visit_type = ?")
            params.append(visit_type)

        return repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params,
        )

    def get_visit(self, visit_id: int) -> dict:
        repo = VisitRecordRepository(self.db)
        row = repo.get_by_id(visit_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
        return dict(row)

    def update_visit(self, visit_id: int, body) -> dict:
        repo = VisitRecordRepository(self.db)
        row = repo.get_by_id(visit_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")

        if body.hcp_id is not None:
            self._check_hcp_exists(body.hcp_id)

        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)

        repo.update(visit_id, updates)
        return dict(repo.get_by_id(visit_id))

    def delete_visit(self, visit_id: int) -> None:
        repo = VisitRecordRepository(self.db)
        row = repo.get_by_id(visit_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
        repo.soft_delete(visit_id)
