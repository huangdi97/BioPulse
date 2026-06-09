"""竞争格局视图 API。"""

from typing import Optional

from fastapi import APIRouter, Query

from pharma_intel.app.services.competitor_landscape_service import (
    get_landscape_matrix,
    get_radar_chart_data,
)

router = APIRouter(prefix="/api/landscape", tags=["竞争格局视图"])


@router.get("/matrix", tags=["竞争格局视图"])
def landscape_matrix(
    therapy_area: Optional[str] = Query(None, description="治疗领域，如 tumor"),
    competitor_ids: Optional[list[str]] = Query(None, description="竞品/公司ID列表"),
):
    return get_landscape_matrix(therapy_area=therapy_area, competitor_ids=competitor_ids)


@router.get("/radar", tags=["竞争格局视图"])
def landscape_radar(target_id: str = Query(..., description="靶点ID")):
    return get_radar_chart_data(target_id)
