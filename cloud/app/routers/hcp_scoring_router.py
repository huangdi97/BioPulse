"""HCP influence scoring APIs."""

from fastapi import APIRouter

from cloud.app.schemas.hcp_scoring import HCPScore
from cloud.app.services.hcp_scoring_service import calculate_score

router = APIRouter(prefix="/api/hcp", tags=["HCP评分"])


@router.get("/{id}/score", response_model=HCPScore, tags=["HCP评分"])
def get_hcp_score(id: str) -> HCPScore:
    return calculate_score(id)
