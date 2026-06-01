from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette import status

from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success
from assistant.app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    """Request model for creating a task."""

    hcp_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Optional[str] = "normal"
    status: Optional[str] = "pending"
    due_date: Optional[str] = None


class TaskUpdate(BaseModel):
    """Request model for updating a task."""

    hcp_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[str] = None


class TaskOut(BaseModel):
    """Response model for a task."""

    id: int
    hcp_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    priority: str
    status: str
    due_date: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[str] = None


@router.post("")
def create_task(
    body: TaskCreate,
    service: TaskService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    """Create a new task."""
    user_id = int(current_user["sub"])
    result = service.create_task(body, user_id)
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("")
def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    hcp_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    service: TaskService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[TaskOut]]:
    """List tasks with pagination and filtering."""
    total, total_pages, rows = service.list_tasks(
        page=page, page_size=page_size,
        hcp_id=hcp_id, status_filter=status_filter, priority=priority,
    )
    items = [TaskOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/{task_id}")
def get_task(
    task_id: int,
    service: TaskService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[TaskOut]:
    """Get a single task by ID."""
    row = service.get_task(task_id)
    return success(data=TaskOut(**row))


@router.patch("/{task_id}")
def update_task(
    task_id: int,
    body: TaskUpdate,
    service: TaskService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[TaskOut]:
    """Update a task."""
    updated = service.update_task(task_id, body)
    return success(data=TaskOut(**updated))


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    service: TaskService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """Delete a task."""
    service.delete_task(task_id)
    return success(message="deleted")
