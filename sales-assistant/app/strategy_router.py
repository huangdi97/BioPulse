"""策略路由：销售策略的CRUD、AI生成、对比与模拟API。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status

from sales_assistant.app.services.strategy_service import StrategyService
from shared.auth_scope import require_scope
from shared.base import ApiResponse, PaginatedResponse, success

router = APIRouter(prefix="/strategies")


class StrategyCreate(BaseModel):
    hcp_name: Optional[str] = None
    visit_date: Optional[str] = None
    goal: Optional[str] = None
    approach: Optional[str] = None
    talking_points: Optional[str] = None
    expected_outcome: Optional[str] = None


class StrategyUpdate(BaseModel):
    hcp_name: Optional[str] = None
    visit_date: Optional[str] = None
    goal: Optional[str] = None
    approach: Optional[str] = None
    talking_points: Optional[str] = None
    expected_outcome: Optional[str] = None
    actual_outcome: Optional[str] = None
    reflection: Optional[str] = None
    effectiveness: Optional[int] = None
    status: Optional[str] = None
    is_active: Optional[int] = None


class StrategyOut(BaseModel):
    id: int
    hcp_name: Optional[str] = None
    visit_date: Optional[str] = None
    goal: Optional[str] = None
    approach: Optional[str] = None
    talking_points: Optional[str] = None
    expected_outcome: Optional[str] = None
    actual_outcome: Optional[str] = None
    reflection: Optional[str] = None
    effectiveness: Optional[int] = None
    status: Optional[str] = None
    is_active: Optional[int] = None
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class StrategyGenerateRequest(BaseModel):
    hcp_name: str
    goal: str
    hcp_tier: Optional[str] = None
    product_name: Optional[str] = None


class StrategySimulateRequest(BaseModel):
    hcp_name: str
    approach: str
    product_name: Optional[str] = None


@router.post("", summary="创建策略", description="创建销售策略", tags=["情报"])
def create_strategy(
    body: StrategyCreate,
    service: StrategyService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    """创建strategy。"""
    user_id = int(current_user["sub"])
    strategy_id = service.create_strategy(body, user_id)
    return JSONResponse(
        content=success(data={"id": strategy_id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("", summary="策略列表", description="获取销售策略列表", tags=["情报"])
def list_strategies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    hcp_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    goal: Optional[str] = Query(None),
    service: StrategyService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[PaginatedResponse[StrategyOut]]:
    """获取strategies。"""
    total, total_pages, rows = service.list_strategies(
        page,
        page_size,
        hcp_name,
        status,
        goal,
    )
    items = [StrategyOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/{strategy_id}", summary="策略详情", description="获取指定策略详情", tags=["情报"])
def get_strategy(
    strategy_id: int,
    service: StrategyService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[StrategyOut]:
    """获取strategy。"""
    row = service.get_strategy(strategy_id)
    return success(data=StrategyOut(**row))


@router.patch("/{strategy_id}", summary="更新策略", description="更新指定策略", tags=["情报"])
def update_strategy(
    strategy_id: int,
    body: StrategyUpdate,
    service: StrategyService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[StrategyOut]:
    """更新strategy。"""
    row = service.update_strategy(strategy_id, body)
    return success(data=StrategyOut(**row))


@router.delete("/{strategy_id}", summary="删除策略", description="删除指定策略", tags=["情报"])
def delete_strategy(
    strategy_id: int,
    service: StrategyService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """删除strategy。"""
    service.delete_strategy(strategy_id)
    return success(message="deleted")


@router.post("/generate", summary="生成策略", description="AI生成销售策略", tags=["情报"])
def generate_strategy(
    body: StrategyGenerateRequest,
    service: StrategyService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    """generate strategy。"""
    user_id = int(current_user["sub"])
    row = service.generate_strategy(body, user_id)
    return JSONResponse(
        content=success(data=StrategyOut(**row)).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/compare", summary="策略对比", description="对比多个销售策略", tags=["情报"])
def compare_strategies(
    ids: str = Query(...),
    service: StrategyService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """compare strategies。"""
    rows = service.compare_strategies(ids)
    strategies = [StrategyOut(**r) for r in rows]
    effs = [r["effectiveness"] for r in rows if r["effectiveness"] is not None]
    goals = list(set(r["goal"] for r in rows if r["goal"]))
    approaches = list(set(r["approach"] for r in rows if r["approach"]))
    return success(
        data={
            "strategies": [s.model_dump() for s in strategies],
            "comparison": {
                "effectiveness_range": f"{min(effs)}-{max(effs)}" if effs else "N/A",
                "common_goals": goals,
                "common_approaches": approaches,
            },
        }
    )


@router.post("/simulate", summary="模拟策略", description="模拟销售策略执行效果", tags=["情报"])
def simulate_strategy(
    body: StrategySimulateRequest,
    service: StrategyService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """simulate strategy。"""
    result = service.simulate_strategy(body)
    return success(data=result)


strategy_root_router = APIRouter()


@strategy_root_router.get("/strategy", summary="策略根路径", description="获取策略根路径")
def get_strategy_root() -> list:
    """获取strategy。"""
    return []
