from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from starlette import status

from shared.auth import get_current_user
from shared.auth_scope import require_scope
from cloud.app.research_database import get_research_db

router = APIRouter(
    prefix="/api/research/pi",
    tags=["科研线"],
    dependencies=[Depends(require_scope("research"))],
)


class PiCreate(BaseModel):
    name: str
    institution: str
    department: str = ""
    title: str = ""
    hcp_id: Optional[int] = None
    research_areas: list[str] = []
    total_papers: int = 0
    total_grants: int = 0
    h_index: int = 0


@router.get("/search")
def search_pi(
    q: str = Query("", description="Search keyword"),
    current_user: dict = Depends(get_current_user),
):
    db = get_research_db()
    try:
        pattern = f"%{q}%"
        rows = db.execute(
            "SELECT * FROM research_pi_profiles WHERE name LIKE ? OR institution LIKE ? OR research_areas LIKE ?",
            (pattern, pattern, pattern),
        ).fetchall()
        return {"code": 0, "data": [dict(r) for r in rows], "message": "success"}
    finally:
        db.close()


@router.get("/{pi_id}")
def get_pi(
    pi_id: int,
    current_user: dict = Depends(get_current_user),
):
    db = get_research_db()
    try:
        row = db.execute("SELECT * FROM research_pi_profiles WHERE pi_id = ?", (pi_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PI not found")
        return {"code": 0, "data": dict(row), "message": "success"}
    finally:
        db.close()


@router.post("", status_code=201)
def create_pi(
    body: PiCreate,
    current_user: dict = Depends(get_current_user),
):
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="name is required")
    import json
    db = get_research_db()
    try:
        cursor = db.execute(
            "INSERT INTO research_pi_profiles (name, hcp_id, institution, department, title, "
            "research_areas, total_papers, total_grants, h_index) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (body.name, body.hcp_id, body.institution, body.department, body.title,
             json.dumps(body.research_areas), body.total_papers, body.total_grants, body.h_index),
        )
        db.commit()
        pi_id = cursor.lastrowid
        row = db.execute("SELECT * FROM research_pi_profiles WHERE pi_id = ?", (pi_id,)).fetchone()
        return {"code": 0, "data": dict(row), "message": "success"}
    finally:
        db.close()
