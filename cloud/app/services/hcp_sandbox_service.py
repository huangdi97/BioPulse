"""HCP沙箱服务，负责医生画像管理与会话行为模拟。"""

import json
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    HcpInteractionsRepository,
    HcpProfilesRepository,
    HcpSimulationsRepository,
)
from cloud.app.services.base import BaseService
from cloud.app.services.sandbox_simulation import SandboxSimulationMixin
from shared.base import PaginatedResponse, validate_columns
from shared.columns import TABLE_HCP_PROFILES_COLS


class HcpSandboxService(SandboxSimulationMixin, BaseService):
    """HCP沙箱服务，提供医生画像管理、会话仿真与AI行为模拟。"""

    def create_profile(
        self,
        name: str,
        title: str,
        hospital: str,
        department: str,
        specialty: str,
        city: str,
        tier: str,
        traits: dict,
        prescription_volume: float,
        influence_score: float,
        digital_engagement: float,
        user_id: int,
    ) -> dict:
        """Create a new HCP (Healthcare Professional) profile.

        Args:
            name: The HCP's name.
            title: The HCP's professional title.
            hospital: The HCP's affiliated hospital.
            department: The HCP's department.
            specialty: The HCP's medical specialty.
            city: The HCP's city.
            tier: The HCP tier classification.
            traits: A dict of behavioral traits.
            prescription_volume: The HCP's prescription volume metric.
            influence_score: The HCP's influence score.
            digital_engagement: The HCP's digital engagement score.
            user_id: The ID of the user creating the profile.

        Returns:
            A dict representing the created HCP profile.
        """
        repo = HcpProfilesRepository(self.db)
        data = {
            "name": name,
            "title": title,
            "hospital": hospital,
            "department": department,
            "specialty": specialty,
            "city": city,
            "tier": tier,
            "traits": json.dumps(traits, ensure_ascii=False),
            "prescription_volume": prescription_volume,
            "influence_score": influence_score,
            "digital_engagement": digital_engagement,
            "created_by": user_id,
        }
        row_id = repo.create(data)
        return repo.get_by_id(row_id)

    def list_profiles(
        self,
        tier: Optional[str] = None,
        specialty: Optional[str] = None,
        city: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """List HCP profiles with optional filtering and pagination.

        Args:
            tier: Optional filter by HCP tier.
            specialty: Optional filter by specialty.
            city: Optional filter by city.
            page: Page number for pagination.
            page_size: Number of items per page.

        Returns:
            A PaginatedResponse containing HCP profile items.
        """
        repo = HcpProfilesRepository(self.db)
        total, total_pages, items = repo.list_filtered(tier=tier, specialty=specialty, city=city, page=page, page_size=page_size)
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_profile(self, hcp_id: int) -> dict:
        """Retrieve a single HCP profile with interaction and simulation counts.

        Args:
            hcp_id: The HCP's ID.

        Returns:
            A dict representing the HCP profile with interaction_count, simulation_count, and last_interaction.

        Raises:
            HTTPException: 404 if the HCP profile is not found.
        """
        profiles_repo = HcpProfilesRepository(self.db)
        interactions_repo = HcpInteractionsRepository(self.db)
        simulations_repo = HcpSimulationsRepository(self.db)
        row = profiles_repo.get_by_id(hcp_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="HCP profile not found")
        row["interaction_count"] = interactions_repo.count_by_hcp_id(hcp_id)
        row["simulation_count"] = simulations_repo.count_by_hcp_id(hcp_id)
        row["last_interaction"] = interactions_repo.get_last_by_hcp_id(hcp_id)
        return row

    def update_profile(
        self,
        hcp_id: int,
        name: Optional[str] = None,
        title: Optional[str] = None,
        hospital: Optional[str] = None,
        department: Optional[str] = None,
        specialty: Optional[str] = None,
        city: Optional[str] = None,
        tier: Optional[str] = None,
        traits: Optional[dict] = None,
        prescription_volume: Optional[float] = None,
        influence_score: Optional[float] = None,
        digital_engagement: Optional[float] = None,
        is_active: Optional[int] = None,
    ) -> dict:
        """Update fields of an existing HCP profile.

        Args:
            hcp_id: The HCP's ID.
            name: Optional new name.
            title: Optional new title.
            hospital: Optional new hospital.
            department: Optional new department.
            specialty: Optional new specialty.
            city: Optional new city.
            tier: Optional new tier.
            traits: Optional new traits dict.
            prescription_volume: Optional new prescription volume.
            influence_score: Optional new influence score.
            digital_engagement: Optional new digital engagement score.
            is_active: Optional active flag (1 for active, 0 for inactive).

        Returns:
            A dict representing the updated HCP profile.

        Raises:
            HTTPException: 404 if the HCP profile is not found.
        """
        repo = HcpProfilesRepository(self.db)
        row = repo.get_by_id(hcp_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="HCP profile not found")
        field_map = {
            "name": name,
            "title": title,
            "hospital": hospital,
            "department": department,
            "specialty": specialty,
            "city": city,
            "tier": tier,
            "prescription_volume": prescription_volume,
            "influence_score": influence_score,
            "digital_engagement": digital_engagement,
            "is_active": is_active,
        }
        upd = {k: v for k, v in field_map.items() if v is not None}
        if traits is not None:
            upd["traits"] = json.dumps(traits, ensure_ascii=False)
        if upd:
            validate_columns(upd, "hcp_profiles", TABLE_HCP_PROFILES_COLS)
            repo.update(hcp_id, upd)
        return repo.get_by_id(hcp_id)

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
