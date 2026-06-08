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
        """Record a new interaction with an HCP.

        Args:
            hcp_id: The HCP's ID.
            interaction_type: The type of interaction (e.g. "visit", "call", "email").
            content: The content of the interaction.
            response: The HCP's response.
            outcome: The interaction outcome.
            strategy_used: The engagement strategy used.
            conducted_at: Optional timestamp of when the interaction occurred.
            user_id: The user ID who conducted the interaction.

        Returns:
            A dict representing the created interaction record.

        Raises:
            HTTPException: 404 if the HCP profile is not found.
        """
        profiles_repo = HcpProfilesRepository(self.db)
        interactions_repo = HcpInteractionsRepository(self.db)
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
        """List interactions for a specific HCP with pagination.

        Args:
            hcp_id: The HCP's ID.
            page: Page number for pagination.
            page_size: Number of items per page.

        Returns:
            A PaginatedResponse containing interaction items.

        Raises:
            HTTPException: 404 if the HCP profile is not found.
        """
        profiles_repo = HcpProfilesRepository(self.db)
        interactions_repo = HcpInteractionsRepository(self.db)
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
