from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette import status

from sales_coach.app.services.module_service import ModuleService
from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success

router = APIRouter(prefix="/modules", tags=["modules"])


class ModuleCreate(BaseModel):
    """Request model for creating a training module."""

    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    difficulty: Optional[str] = "beginner"


class ModuleUpdate(BaseModel):
    """Request model for updating a training module."""

    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    difficulty: Optional[str] = None
    is_active: Optional[int] = None


class ModuleOut(BaseModel):
    """Response model for a training module."""

    id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    difficulty: str
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("")
def create_module(
    body: ModuleCreate,
    service: ModuleService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    """Create a new training module."""
    user_id = int(current_user["sub"])
    result = service.create(body, user_id)
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("")
def list_modules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    service: ModuleService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[ModuleOut]]:
    """List training modules with pagination and filtering."""
    total, total_pages, rows = service.list(page, page_size, category, difficulty)
    items = [ModuleOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/{module_id}")
def get_module(
    module_id: int,
    service: ModuleService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[ModuleOut]:
    """Get a single training module by ID."""
    row = service.get(module_id)
    return success(data=ModuleOut(**row))


@router.patch("/{module_id}")
def update_module(
    module_id: int,
    body: ModuleUpdate,
    service: ModuleService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[ModuleOut]:
    """Update a training module."""
    updated = service.update(module_id, body)
    return success(data=ModuleOut(**updated))


@router.delete("/{module_id}")
def delete_module(
    module_id: int,
    service: ModuleService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """Soft-delete a training module by setting is_active to 0."""
    service.delete(module_id)
    return success(message="deleted")
