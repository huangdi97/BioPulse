"""商机因果归因路由。"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from starlette import status

from cloud.app.services import CausalAttributionService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/opportunities/attribution", tags=["商机因果归因"])


class AttributionFactorItem(BaseModel):
    """AttributionFactorItem 服务类。"""

    name: str
    impact: float
    direction: str
    weight: float


class AttributionResponse(BaseModel):
    """AttributionResponse 服务类。"""

    opportunity_id: int
    total_score: float
    confidence: float
    factors: list[AttributionFactorItem]
    factor_count: int
    top_factor_name: str
    recommendation: str
    model_version: str
    created_at: str
    updated_at: str


class FactorMetaItem(BaseModel):
    """FactorMetaItem 服务类。"""

    name: str
    display_name: str
    max_score: int
    description: str


class FactorsResponse(BaseModel):
    """FactorsResponse 服务类。"""

    factors: list[FactorMetaItem]


class SimulateRequest(BaseModel):
    """SimulateRequest 服务类。"""

    what_if: dict[str, float]


@router.get("/{opp_id}", summary="Get Attribution by ID", description="根据商机ID获取归因分析结果", tags=["商机因果归因"])
def get_attribution(
    opp_id: int,
    current_user: dict = Depends(require_scope(["pharma", "research"])),
    service: CausalAttributionService = Depends(),
):
    """get_attribution 操作。

    Args:
        opp_id: 描述
        current_user: 描述
        service: 描述
    """
    try:
        data = service.get_attribution(opp_id)
    except Exception:
        logger.exception("Causal attribution路由异常")
        data = service.refresh_attribution(opp_id)
    return success(data=data)


@router.post(
    "/{opp_id}/refresh", status_code=status.HTTP_200_OK, summary="Refresh Attribution", description="刷新指定商机的归因分析", tags=["商机因果归因"]
)
def refresh_attribution(
    opp_id: int,
    current_user: dict = Depends(require_scope(["pharma", "research"])),
    service: CausalAttributionService = Depends(),
):
    """refresh_attribution 操作。

    Args:
        opp_id: 描述
        current_user: 描述
        service: 描述
    """
    data = service.refresh_attribution(opp_id)
    return success(data=data)


@router.get("/factors", summary="List all Factors", description="获取所有可用的归因因子列表", tags=["商机因果归因"])
def list_factors(
    current_user: dict = Depends(require_scope(["pharma", "research"])),
    service: CausalAttributionService = Depends(),
):
    """list_factors 操作。

    Args:
        current_user: 描述
        service: 描述
    """
    data = service.list_factors()
    return success(data={"factors": data})


@router.post("/{opp_id}/simulate", summary="Simulate Attribution", description="对指定商机模拟假设场景的归因结果", tags=["商机因果归因"])
def simulate_attribution(
    opp_id: int,
    body: SimulateRequest,
    current_user: dict = Depends(require_scope(["pharma", "research"])),
    service: CausalAttributionService = Depends(),
):
    """simulate_attribution 操作。

    Args:
        opp_id: 描述
        current_user: 描述
        service: 描述
    """
    data = service.simulate_outcome(opp_id, body.what_if)
    return success(data=data)
