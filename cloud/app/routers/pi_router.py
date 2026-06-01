from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from starlette import status
from shared.auth import get_current_user
from cloud.app.dependencies import get_db
from cloud.app.repositories.pi_repository import PiRepository

router = APIRouter(prefix="/api/pi", tags=["pi"])


class PiCreate(BaseModel):
    """Request body for creating a new PI profile."""
    name: str
    institution: str
    department: str = ""
    title: str = ""
    hcp_id: Optional[int] = None
    research_areas: list[str] = []
    total_papers: int = 0
    total_grants: int = 0
    h_index: int = 0


class PiUpdate(BaseModel):
    """Request body for updating an existing PI profile."""
    name: Optional[str] = None
    institution: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    hcp_id: Optional[int] = None
    research_areas: Optional[list[str]] = None
    total_papers: Optional[int] = None
    total_grants: Optional[int] = None
    h_index: Optional[int] = None


@router.get("/search")
def search_pi(q: str = Query("", description="Search keyword"),
              current_user: dict = Depends(get_current_user),
              db=Depends(get_db)):
    """Search PI profiles by name, institution, or research area."""
    repo = PiRepository(db)
    results = repo.search(q)
    return {"code": 0, "data": results, "message": "success"}


@router.get("/{pi_id}")
def get_pi(pi_id: int, current_user: dict = Depends(get_current_user),
           db=Depends(get_db)):
    """Get a single PI profile by ID."""
    repo = PiRepository(db)
    pi = repo.get_by_id(pi_id)
    if not pi:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PI not found")
    return {"code": 0, "data": pi, "message": "success"}


@router.post("", status_code=201)
def create_pi(body: PiCreate, current_user: dict = Depends(get_current_user),
              db=Depends(get_db)):
    """Create a new PI profile."""
    repo = PiRepository(db)
    pi_id = repo.create(
        name=body.name, institution=body.institution,
        department=body.department, title=body.title,
        hcp_id=body.hcp_id, research_areas=body.research_areas,
        total_papers=body.total_papers, total_grants=body.total_grants,
        h_index=body.h_index,
    )
    pi = repo.get_by_id(pi_id)
    return {"code": 0, "data": pi, "message": "success"}


@router.put("/{pi_id}")
def update_pi(pi_id: int, body: PiUpdate,
              current_user: dict = Depends(get_current_user),
              db=Depends(get_db)):
    """Update an existing PI profile. Only provided fields will be updated."""
    repo = PiRepository(db)
    kwargs = {k: v for k, v in body.model_dump().items() if v is not None}
    if not kwargs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    repo.update(pi_id, **kwargs)
    pi = repo.get_by_id(pi_id)
    return {"code": 0, "data": pi, "message": "success"}
