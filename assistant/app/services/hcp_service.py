from typing import Optional

from fastapi import HTTPException
from starlette import status

from assistant.app.repositories import HcpRepository
from assistant.app.services.base import BaseService


class HcpService(BaseService):
    def create_hcp(self, body, user_id: int) -> dict:
        repo = HcpRepository(self.db)
        row_id = repo.create(
            body.model_dump(),
            extra={"created_by": user_id},
        )
        return {"id": row_id}

    def list_hcps(
        self,
        page: int,
        page_size: int,
        name: Optional[str] = None,
        hospital: Optional[str] = None,
        department: Optional[str] = None,
        level: Optional[str] = None,
    ) -> tuple:
        repo = HcpRepository(self.db)
        conditions = ["is_active = 1"]
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
        if level:
            conditions.append("level = ?")
            params.append(level)

        return repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params,
        )

    def get_hcp(self, hcp_id: int) -> dict:
        repo = HcpRepository(self.db)
        row = repo.get_by_id(hcp_id)
        if not row or row["is_active"] != 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
        return dict(row)

    def update_hcp(self, hcp_id: int, body) -> dict:
        repo = HcpRepository(self.db)
        row = repo.get_by_id(hcp_id)
        if not row or row["is_active"] != 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)
        repo.update(hcp_id, updates)
        return dict(repo.get_by_id(hcp_id))

    def delete_hcp(self, hcp_id: int) -> None:
        repo = HcpRepository(self.db)
        row = repo.get_by_id(hcp_id)
        if not row or row["is_active"] != 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")
        repo.soft_delete(hcp_id)
