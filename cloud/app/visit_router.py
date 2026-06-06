"""拜访记录路由。"""

import sqlite3

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from cloud.app.database import DB_PATH
from cloud.app.repositories.visit_repository import VisitRepository
from cloud.app.services.visit_service import VisitService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="", tags=["拜访"])


class VisitCreate(BaseModel):
    hcp_id: int
    hcp_name: str
    content: str
    visit_type: str = ""
    evidence_photos: list[str] = []
    location: str = ""
    location_mode: str = ""


@router.post("/visit")
def create_visit(body: VisitCreate, user: dict = Depends(require_scope("visit"))):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        repo = VisitRepository(conn)
        service = VisitService(repo)
        record = service.create_visit(body)
        return success(data=record)
    finally:
        conn.close()


@router.get("/visit/{visit_id}")
def get_visit(visit_id: int, user: dict = Depends(require_scope("visit"))):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        repo = VisitRepository(conn)
        service = VisitService(repo)
        record = service.get_visit(visit_id)
        return success(data=record)
    finally:
        conn.close()
