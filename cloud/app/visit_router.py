from sqlite3 import Connection

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from cloud.app.database import get_db
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
def create_visit(body: VisitCreate, conn: Connection = Depends(get_db), user: dict = Depends(require_scope("visit"))):
    """创建visit。"""
    service = VisitService(conn)
    record = service.create_visit(body)
    return success(data=record)


@router.get("/visit/{visit_id}")
def get_visit(visit_id: int, conn: Connection = Depends(get_db), user: dict = Depends(require_scope("visit"))):
    """获取visit。"""
    service = VisitService(conn)
    record = service.get_visit(visit_id)
    return success(data=record)
