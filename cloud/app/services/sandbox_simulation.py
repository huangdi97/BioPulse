"""HCP 沙箱模拟方法。"""

from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import HcpInteractionsRepository, HcpProfilesRepository, HcpSimulationsRepository
from cloud.app.services.hcp_simulation_core import _call_ai, build_simulation_record
from shared.base import PaginatedResponse


class SandboxSimulationMixin:
    """HCP 行为模拟记录和统计方法。"""

    def simulate(self, hcp_id: int, scenario: str, strategy: str, user_id: int) -> dict:
        """Run an AI-powered simulation of an HCP interaction.

        Uses the HCP's profile traits, recent interactions, and an AI call to generate
        a simulated conversation outcome.

        Args:
            hcp_id: The HCP's ID.
            scenario: The simulation scenario description.
            strategy: The engagement strategy to simulate.
            user_id: The user ID initiating the simulation.

        Returns:
            A dict representing the created simulation record.

        Raises:
            HTTPException: 404 if the HCP profile is not found.
        """
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
        """List simulation records with optional filtering and pagination.

        Args:
            hcp_id: Optional filter by HCP ID.
            status: Optional filter by simulation status.
            page: Page number for pagination.
            page_size: Number of items per page.

        Returns:
            A PaginatedResponse containing simulation items.
        """
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
        """Retrieve a single simulation record by ID.

        Args:
            sim_id: The simulation ID.

        Returns:
            A dict representing the simulation record.

        Raises:
            HTTPException: 404 if the simulation is not found.
        """
        repo = HcpSimulationsRepository(self.db)
        row = repo.get_by_id(sim_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Simulation not found")
        return row

    def dashboard(self) -> dict:
        """Retrieve aggregated HCP sandbox statistics for the dashboard.

        Returns:
            A dict with total_hcp, tier_distribution, total_simulations, and recent_simulations.
        """
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
