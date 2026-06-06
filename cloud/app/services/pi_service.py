"""PI 服务，负责学术 PI 信息的搜索、创建与更新。"""

from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories.pi_repository import PiRepository
from cloud.app.services.base import BaseService


class PiService(BaseService):
    """PI 服务，提供学术 PI 的搜索、详情查询、创建与更新。"""

    def search(self, q: str) -> list:
        repo = PiRepository(self.db)
        return repo.search(q)

    def get_by_id(self, pi_id: int) -> dict:
        repo = PiRepository(self.db)
        pi = repo.get_by_id(pi_id)
        if not pi:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PI not found")
        return pi

    def create(
        self,
        name: str,
        institution: str,
        department: str = "",
        title: str = "",
        hcp_id: Optional[int] = None,
        research_areas: list | None = None,
        total_papers: int = 0,
        total_grants: int = 0,
        h_index: int = 0,
    ) -> dict:
        repo = PiRepository(self.db)
        pi_id = repo.create(
            name=name,
            institution=institution,
            department=department,
            title=title,
            hcp_id=hcp_id,
            research_areas=research_areas,
            total_papers=total_papers,
            total_grants=total_grants,
            h_index=h_index,
        )
        return repo.get_by_id(pi_id)

    def update(self, pi_id: int, **kwargs) -> dict:
        repo = PiRepository(self.db)
        if not kwargs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )
        repo.update(pi_id, **kwargs)
        pi = repo.get_by_id(pi_id)
        return pi
