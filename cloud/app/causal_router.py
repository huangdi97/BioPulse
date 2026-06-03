from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from starlette import status

from cloud.app.services.causal_service import CausalService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/causal", tags=["因果推理"])


class GraphBuild(BaseModel):
    decision_id: str
    include_metrics: bool = True


class CounterfactualSimulate(BaseModel):
    strategy_id: str
    scenarios: list[dict] = []


class CausalInfer(BaseModel):
    features: dict
    target: str
    method: str = "linear"


class HcpPrescription(BaseModel):
    hcp_entity_id: str
    factors: list[str] = []
    date_range: dict = {}


@router.post("/graph/build", status_code=status.HTTP_201_CREATED)
def build_graph(
    body: GraphBuild,
    current_user: dict = Depends(require_scope("visit")),
    service: CausalService = Depends(),
):
    """构建因果图。"""
    user_id = int(current_user["sub"])
    result = service.build_graph(
        decision_id=body.decision_id,
        include_metrics=body.include_metrics,
        user_id=user_id,
    )
    return success(data=result)


@router.get("/graph/{graph_id}")
def get_graph(
    graph_id: str,
    current_user: dict = Depends(require_scope("visit")),
    service: CausalService = Depends(),
):
    """获取因果图详情。"""
    result = service.get_graph(graph_id)
    return success(data=result)


@router.post("/counterfactual/simulate", status_code=status.HTTP_201_CREATED)
def simulate_counterfactual(
    body: CounterfactualSimulate,
    current_user: dict = Depends(require_scope("visit")),
    service: CausalService = Depends(),
):
    """模拟反事实场景。"""
    user_id = int(current_user["sub"])
    result = service.simulate_counterfactual(
        strategy_id=body.strategy_id,
        scenarios=body.scenarios,
        user_id=user_id,
    )
    return success(data=result)


@router.get("/counterfactual/list")
def list_counterfactuals(
    strategy_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_scope("visit")),
    service: CausalService = Depends(),
):
    """分页列出反事实模拟记录。"""
    result = service.list_counterfactuals(
        strategy_id=strategy_id,
        page=page,
        page_size=page_size,
    )
    return success(data=result)


@router.post("/infer")
def causal_infer(
    body: CausalInfer,
    current_user: dict = Depends(require_scope("visit")),
    service: CausalService = Depends(),
):
    """执行因果推断。"""
    result = service.causal_infer(
        features=body.features,
        target=body.target,
        method=body.method,
    )
    return success(data=result)


@router.post("/hcp/prescription")
def hcp_prescription_attribution(
    body: HcpPrescription,
    current_user: dict = Depends(require_scope("visit")),
    service: CausalService = Depends(),
):
    """归因 HCP 处方影响因素。"""
    result = service.hcp_prescription_attribution(
        hcp_entity_id=body.hcp_entity_id,
        factors=body.factors,
        date_range=body.date_range,
    )
    return success(data=result)
