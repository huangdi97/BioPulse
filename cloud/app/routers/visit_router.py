"""拜访记录路由。"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

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


@router.post("/visit", tags=["拜访"])
def create_visit(body: VisitCreate, user: dict = Depends(require_scope("visit"))):
    service = VisitService()
    record = service.create_visit(body)
    return success(data=record)


@router.get("/visit/{visit_id}", tags=["拜访"])
def get_visit(visit_id: int, user: dict = Depends(require_scope("visit"))):
    service = VisitService()
    record = service.get_visit(visit_id)
    return success(data=record)
