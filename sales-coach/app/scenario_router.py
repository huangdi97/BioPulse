from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette import status

from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success
from sales_coach.app.scenario_library import (
    FIXED_SCENARIOS,
    get_scenarios_by_category,
    get_scenario_by_difficulty,
)
from sales_coach.app.services.scenario_service import ScenarioService

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


class ScenarioCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    role_setting: Optional[str] = None
    goal: Optional[str] = None
    difficulty: Optional[str] = "medium"
    category: Optional[str] = None
    content: Optional[str] = None
    tips: Optional[str] = None


class ScenarioUpdate(BaseModel):
    title: Optional[str] = None
    role_setting: Optional[str] = None
    goal: Optional[str] = None
    difficulty: Optional[str] = None
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
    category: Optional[str] = None
    content: Optional[str] = None
    tips: Optional[str] = None
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("")
def create_scenario(
    body: ScenarioCreate,
    service: ScenarioService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    """Create a new coach scenario."""
    user_id = int(current_user["sub"])
    result = service.create(body, user_id)
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("")
def list_scenarios(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    service: ScenarioService = Depends(),
    current_user: dict = Depends(get_current_user),
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


@router.get("/types")
def get_scenario_types(
    current_user: dict = Depends(get_current_user),
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


@router.get("/by-category/{category}")
def list_scenarios_by_category(
    category: str,
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """Return all fixed scenarios matching the given category."""
    scenarios = get_scenarios_by_category(category)
    return success(data={"category": category, "scenarios": scenarios, "count": len(scenarios)})


@router.get("/by-difficulty/{difficulty}")
def list_scenarios_by_difficulty(
    difficulty: str,
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """Return all fixed scenarios matching the given difficulty level."""
    scenarios = get_scenario_by_difficulty(difficulty)
    return success(data={"difficulty": difficulty, "scenarios": scenarios, "count": len(scenarios)})


@router.get("/{scenario_id}")
def get_scenario(
    scenario_id: int,
    service: ScenarioService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[ScenarioOut]:
    """Get a single coach scenario by ID."""
    row = service.get(scenario_id)
    return success(data=ScenarioOut(**row))


@router.patch("/{scenario_id}")
def update_scenario(
    scenario_id: int,
    body: ScenarioUpdate,
    service: ScenarioService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[ScenarioOut]:
    """Update a coach scenario."""
    updated = service.update(scenario_id, body)
    return success(data=ScenarioOut(**updated))


@router.delete("/{scenario_id}")
def delete_scenario(
    scenario_id: int,
    service: ScenarioService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """Soft-delete a coach scenario by setting is_active to 0."""
    service.delete(scenario_id)
    return success(message="deleted")
