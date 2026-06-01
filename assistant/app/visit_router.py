from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette import status

from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success
from assistant.app.database import get_db
from assistant.app.repositories import HcpRepository, VisitRecordRepository

router = APIRouter(prefix="/visits", tags=["visits"])


class VisitCreate(BaseModel):
    """Request model for creating a visit record."""

    hcp_id: int
    visit_type: Optional[str] = None
    summary: Optional[str] = Field(None, max_length=2000)
    # outcome: Optional[str] = Field(None, max_length=500)
    detail: Optional[str] = None
    feedback: Optional[str] = None
    next_action: Optional[str] = None
    mood: Optional[str] = None
    is_completed: Optional[int] = 1
    visit_date: Optional[str] = None


class VisitUpdate(BaseModel):
    """Request model for updating a visit record."""

    hcp_id: Optional[int] = None
    visit_type: Optional[str] = None
    summary: Optional[str] = None
    detail: Optional[str] = None
    feedback: Optional[str] = None
    next_action: Optional[str] = None
    mood: Optional[str] = None
    is_completed: Optional[int] = None
    visit_date: Optional[str] = None


class VisitOut(BaseModel):
    """Response model for a visit record."""

    id: int
    hcp_id: int
    visit_type: Optional[str] = None
    summary: Optional[str] = None
    detail: Optional[str] = None
    feedback: Optional[str] = None
    next_action: Optional[str] = None
    mood: Optional[str] = None
    is_completed: int
    visit_date: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[str] = None


def _check_hcp_exists(db, hcp_id: int) -> None:
    """Raise 404 if the referenced HCP does not exist or is inactive."""
    repo = HcpRepository(db)
    row = repo.get_by_id(hcp_id)
    if not row or row["is_active"] != 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found"
        )


@router.post("")
def create_visit(
    body: VisitCreate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    """Create a new visit record."""
    _check_hcp_exists(db, body.hcp_id)
    repo = VisitRecordRepository(db)
    user_id = int(current_user["sub"])
    row_id = repo.create(
        body.model_dump(),
        extra={"created_by": user_id},
    )
    return JSONResponse(
        content=success(data={"id": row_id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("")
def list_visits(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    hcp_id: Optional[int] = Query(None),
    visit_type: Optional[str] = Query(None),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[VisitOut]]:
    """List visit records with pagination and filtering."""
    repo = VisitRecordRepository(db)
    conditions: List[str] = []
    params: list = []

    if hcp_id is not None:
        conditions.append("hcp_id = ?")
        params.append(hcp_id)
    if visit_type:
        conditions.append("visit_type = ?")
        params.append(visit_type)

    total, total_pages, rows = repo.paginate(
        page=page,
        page_size=page_size,
        conditions=conditions,
        params=params,
    )
    items = [VisitOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/{visit_id}")
def get_visit(
    visit_id: int,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[VisitOut]:
    """Get a single visit record by ID."""
    repo = VisitRecordRepository(db)
    row = repo.get_by_id(visit_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found"
        )
    return success(data=VisitOut(**dict(row)))


@router.patch("/{visit_id}")
def update_visit(
    visit_id: int,
    body: VisitUpdate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[VisitOut]:
    """Update a visit record."""
    repo = VisitRecordRepository(db)
    row = repo.get_by_id(visit_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found"
        )

    if body.hcp_id is not None:
        _check_hcp_exists(db, body.hcp_id)

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        return success(data=VisitOut(**dict(row)))

    repo.update(visit_id, updates)
    updated = repo.get_by_id(visit_id)
    return success(data=VisitOut(**dict(updated)))


@router.delete("/{visit_id}")
def delete_visit(
    visit_id: int,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """Delete a visit record."""
    repo = VisitRecordRepository(db)
    row = repo.get_by_id(visit_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found"
        )
    repo.soft_delete(visit_id)
    return success(message="deleted")
