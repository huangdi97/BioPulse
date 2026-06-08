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
from cloud.app.services.hcp_simulation_core import _call_ai, build_simulation_record
from shared.base import PaginatedResponse, validate_columns
from shared.columns import TABLE_HCP_PROFILES_COLS


class HcpSandboxService(BaseService):
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

    def simulate(self, hcp_id: int, scenario: str, strategy: str, user_id: int) -> dict:
        profiles_repo = HcpProfilesRepository(self.db)
        interactions_repo = HcpInteractionsRepository(self.db)
        simulations_repo = HcpSimulationsRepository(self.db)
        hcp_row = profiles_repo.get_by_id(hcp_id)
        if not hcp_row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="HCP profile not found")
        int_rows = interactions_repo.get_recent_by_hcp_id(hcp_id, limit=5)
        data = build_simulation_record(hcp_id, hcp_row, int_rows, scenario, strategy, user_id, call_ai=_call_ai)
        row_id = simulations_repo.create(data)
        return simulations_repo.get_by_id(row_id)

    def list_simulations(
        self,
        hcp_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        repo = HcpSimulationsRepository(self.db)
        total, total_pages, items = repo.list_filtered(hcp_id=hcp_id, status_=status, page=page, page_size=page_size)
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_simulation(self, sim_id: int) -> dict:
        repo = HcpSimulationsRepository(self.db)
        row = repo.get_by_id(sim_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Simulation not found")
        return row

    def dashboard(self) -> dict:
        profiles_repo = HcpProfilesRepository(self.db)
        simulations_repo = HcpSimulationsRepository(self.db)
        total = profiles_repo.count_active()
        tier_dist = profiles_repo.tier_distribution()
        sim_total = simulations_repo.count_all()
        recent = simulations_repo.get_recent(limit=5)
        return {
            "total_hcp": total,
            "tier_distribution": tier_dist,
            "total_simulations": sim_total,
            "recent_simulations": recent,
        }
