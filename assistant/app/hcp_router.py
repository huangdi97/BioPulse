from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette import status

from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success
from assistant.app.database import get_db
from assistant.app.repositories import HcpRepository

router = APIRouter(prefix="/hcp", tags=["hcp"])


class HcpCreate(BaseModel):
    """Request model for creating an HCP record."""

    name: str = Field(..., min_length=1, max_length=100)
    hospital: str
    department: Optional[str] = None
    title: Optional[str] = None
    specialty: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    wechat: Optional[str] = None
    email: Optional[str] = Field(None, max_length=100)
    level: Optional[str] = "C"


class HcpUpdate(BaseModel):
    """Request model for updating an HCP record."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    hospital: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    specialty: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    wechat: Optional[str] = None
    email: Optional[str] = Field(None, max_length=100)
    level: Optional[str] = None
    is_active: Optional[int] = None


class HcpOut(BaseModel):
    """Response model for an HCP record."""

    id: int
    name: str
    hospital: str
    department: Optional[str] = None
    title: Optional[str] = None
    specialty: Optional[str] = None
    phone: Optional[str] = None
    wechat: Optional[str] = None
    email: Optional[str] = None
    level: str
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("")
def create_hcp(
    body: HcpCreate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    """Create a new HCP record."""
    repo = HcpRepository(db)
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
def list_hcps(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: Optional[str] = Query(None),
    hospital: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[HcpOut]]:
    """List HCP records with pagination and filtering."""
    repo = HcpRepository(db)
    conditions = ["is_active = 1"]
    params: list = []

    if name:
        conditions.append("name LIKE ?")
        params.append(f"%{name}%")
    if hospital:
        conditions.append("hospital LIKE ?")
        params.append(f"%{hospital}%")
    if department:
        conditions.append("department LIKE ?")
        params.append(f"%{department}%")
    if level:
        conditions.append("level = ?")
        params.append(level)

    total, total_pages, rows = repo.paginate(
        page=page,
        page_size=page_size,
        conditions=conditions,
        params=params,
    )
    items = [HcpOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/{hcp_id}")
def get_hcp(
    hcp_id: int,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[HcpOut]:
    """Get a single HCP record by ID."""
    repo = HcpRepository(db)
    row = repo.get_by_id(hcp_id)
    if not row or row["is_active"] != 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found"
        )
    return success(data=HcpOut(**dict(row)))


@router.patch("/{hcp_id}")
def update_hcp(
    hcp_id: int,
    body: HcpUpdate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[HcpOut]:
    """Update an HCP record."""
    repo = HcpRepository(db)
    row = repo.get_by_id(hcp_id)
    if not row or row["is_active"] != 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found"
        )

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        return success(data=HcpOut(**dict(row)))

    repo.update(hcp_id, updates)
    updated = repo.get_by_id(hcp_id)
    return success(data=HcpOut(**dict(updated)))


@router.delete("/{hcp_id}")
def delete_hcp(
    hcp_id: int,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """Soft-delete an HCP record by setting is_active to 0."""
    repo = HcpRepository(db)
    row = repo.get_by_id(hcp_id)
    if not row or row["is_active"] != 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found"
        )
    repo.soft_delete(hcp_id)
    return success(message="deleted")
