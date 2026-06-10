"""场景路由模块，提供教练场景的CRUD、分类筛选和难度筛选接口。"""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette import status

from sales_coach.app.scenario_library import (
    FIXED_SCENARIOS,
    get_scenario_by_difficulty,
    get_scenarios_by_category,
)
from sales_coach.app.schemas.scenario import ScenarioRecommendation
from sales_coach.app.services.scenario_recommender import recommend_scenario
from sales_coach.app.services.scenario_service import ScenarioService
from shared.auth_scope import require_scope
from shared.base import ApiResponse, PaginatedResponse, success

router = APIRouter(prefix="/scenarios")
api_router = APIRouter(prefix="/api/scenario", tags=["场景"])


class ScenarioCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    role_setting: Optional[str] = None
    goal: Optional[str] = None
    difficulty: Optional[str] = "medium"
    difficulty_level: Optional[Literal["beginner", "intermediate", "advanced"]] = None
    prerequisites: list[str] = Field(default_factory=list)
    category: Optional[str] = None
    content: Optional[str] = None
    tips: Optional[str] = None


class ScenarioUpdate(BaseModel):
    title: Optional[str] = None
    role_setting: Optional[str] = None
    goal: Optional[str] = None
    difficulty: Optional[str] = None
    difficulty_level: Optional[Literal["beginner", "intermediate", "advanced"]] = None
    prerequisites: Optional[list[str]] = None
    category: Optional[str] = None
    content: Optional[str] = None
    tips: Optional[str] = None
    is_active: Optional[int] = None


class ScenarioOut(BaseModel):
    id: int
    title: str
    role_setting: Optional[str] = None
    goal: Optional[str] = None
    difficulty: str
    difficulty_level: Optional[Literal["beginner", "intermediate", "advanced"]] = None
    prerequisites: list[str] = Field(default_factory=list)
    category: Optional[str] = None
    content: Optional[str] = None
    tips: Optional[str] = None
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@api_router.get("/recommend", summary="推荐训练场景", description="基于历史评估分数推荐匹配难度场景")
def recommend_training_scenario(user_id: str = Query(...)) -> ApiResponse[ScenarioRecommendation]:
    """根据用户历史评分推荐场景。"""
    return success(data=recommend_scenario(user_id))


@router.post("", summary="创建场景", description="创建新的教练场景", tags=["场景"])
def create_scenario(
    body: ScenarioCreate,
    service: ScenarioService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    """Create a new coach scenario."""
    user_id = int(current_user["sub"])
    result = service.create(body, user_id)
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("", summary="场景列表", description="分页查询教练场景，支持分类和难度筛选", tags=["场景"])
def list_scenarios(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    service: ScenarioService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[PaginatedResponse[ScenarioOut]]:
    """List coach scenarios with pagination and filtering."""
    total, total_pages, rows = service.list(page, page_size, category, difficulty)
    items = [ScenarioOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/types", summary="场景类型", description="获取可用的场景分类和难度级别", tags=["场景"])
def get_scenario_types(
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """Return available scenario categories and difficulty levels."""
    categories = sorted(set(s["category"] for s in FIXED_SCENARIOS))
    difficulties = sorted(set(s["difficulty"] for s in FIXED_SCENARIOS))
    return success(
        data={
            "categories": categories,
            "difficulties": difficulties,
            "total_fixed_scenarios": len(FIXED_SCENARIOS),
        }
    )


@router.get("/by-category/{category}", summary="分类筛选", description="按分类获取固定场景列表", tags=["场景"])
def list_scenarios_by_category(
    category: str,
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """Return all fixed scenarios matching the given category."""
    scenarios = get_scenarios_by_category(category)
    return success(data={"category": category, "scenarios": scenarios, "count": len(scenarios)})


@router.get("/by-difficulty/{difficulty}", summary="难度筛选", description="按难度级别获取固定场景列表", tags=["场景"])
def list_scenarios_by_difficulty(
    difficulty: str,
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """Return all fixed scenarios matching the given difficulty level."""
    scenarios = get_scenario_by_difficulty(difficulty)
    return success(data={"difficulty": difficulty, "scenarios": scenarios, "count": len(scenarios)})


@router.get("/{scenario_id}", summary="场景详情", description="根据ID获取教练场景详情", tags=["场景"])
def get_scenario(
    scenario_id: int,
    service: ScenarioService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[ScenarioOut]:
    """Get a single coach scenario by ID."""
    row = service.get(scenario_id)
    return success(data=ScenarioOut(**row))


@router.patch("/{scenario_id}", summary="更新场景", description="更新指定的教练场景信息", tags=["场景"])
def update_scenario(
    scenario_id: int,
    body: ScenarioUpdate,
    service: ScenarioService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[ScenarioOut]:
    """Update a coach scenario."""
    updated = service.update(scenario_id, body)
    return success(data=ScenarioOut(**updated))


@router.delete("/{scenario_id}", summary="删除场景", description="软删除指定的教练场景", tags=["场景"])
def delete_scenario(
    scenario_id: int,
    service: ScenarioService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """Soft-delete a coach scenario by setting is_active to 0."""
    service.delete(scenario_id)
    return success(message="deleted")
