"""HCP 沙箱模拟执行方法。"""

from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import HcpInteractionsRepository, HcpProfilesRepository
from shared.base import PaginatedResponse


class HcpSandboxSimMixin:
    """HCP 沙箱模拟执行方法，提供交互记录功能。"""

    def create_interaction(
        self,
        hcp_id: int,
        interaction_type: str,
        content: str,
        response: str,
        outcome: str,
        strategy_used: str,
        conducted_at: Optional[str],
        user_id: int,
    ) -> dict:
        conn = self._connection()
        profiles_repo = HcpProfilesRepository(conn)
        interactions_repo = HcpInteractionsRepository(conn)
        if not profiles_repo.get_by_id(hcp_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="HCP profile not found")
        data = {
            "hcp_id": hcp_id,
            "interaction_type": interaction_type,
            "content": content,
            "response": response,
            "outcome": outcome,
            "strategy_used": strategy_used,
            "conducted_by": user_id,
            "conducted_at": conducted_at,
        }
        row_id = interactions_repo.create(data)
        return interactions_repo.get_by_id(row_id)

    def list_interactions(self, hcp_id: int, page: int = 1, page_size: int = 20) -> PaginatedResponse:
        conn = self._connection()
        profiles_repo = HcpProfilesRepository(conn)
        interactions_repo = HcpInteractionsRepository(conn)
        if not profiles_repo.get_by_id(hcp_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="HCP profile not found")
        total, total_pages, items = interactions_repo.list_by_hcp_id(hcp_id, page=page, page_size=page_size)
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
