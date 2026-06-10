"""Competitor quicklook APIs."""

from fastapi import APIRouter, Depends, Query

from sales_assistant.app.schemas.competitor_quicklook import QuicklookDashboard
from sales_assistant.app.services.competitor_quicklook_service import get_quicklook
from shared.auth_scope import require_scope

router = APIRouter(prefix="/api/competitor", tags=["竞品速查"])


@router.get("/quicklook", response_model=QuicklookDashboard, tags=["竞品速查"])
def quicklook(hcp_id: str = Query(..., description="HCP identifier"), _: dict = Depends(require_scope("visit"))) -> QuicklookDashboard:
    return get_quicklook(hcp_id)
