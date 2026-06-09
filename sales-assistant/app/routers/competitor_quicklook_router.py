"""Competitor quicklook APIs."""

from fastapi import APIRouter, Query

from sales_assistant.app.schemas.competitor_quicklook import QuicklookDashboard
from sales_assistant.app.services.competitor_quicklook_service import get_quicklook

router = APIRouter(prefix="/api/competitor", tags=["竞品速查"])


@router.get("/quicklook", response_model=QuicklookDashboard, tags=["竞品速查"])
def quicklook(hcp_id: str = Query(..., description="HCP identifier")) -> QuicklookDashboard:
    return get_quicklook(hcp_id)
