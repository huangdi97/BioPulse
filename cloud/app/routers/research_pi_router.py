"""科研 PI 路由：研究者搜索、详情、创建与审计日志。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from cloud.app.services.research_pi_service import ResearchPiService
from cloud.app.services.research_service import ResearchService
from shared.auth import get_current_user
from shared.auth_scope import require_scope

router = APIRouter(
    prefix="/api/research/pi",
    tags=["科研线"],
    dependencies=[Depends(require_scope("research"))],
)


class PiCreate(BaseModel):
    """科研 PI 创建请求体。"""

    name: str
    institution: str
    department: str = ""
    title: str = ""
    hcp_id: Optional[int] = None
    research_areas: list[str] = []
    total_papers: int = 0
    total_grants: int = 0
    h_index: int = 0


@router.get("/search", tags=["Research Pi"])
def search_pi(
    q: str = Query("", description="Search keyword"),
    current_user: dict = Depends(get_current_user),
):
    service = ResearchPiService()
    results = service.search(q)
    return {"code": 0, "data": results, "message": "success"}


@router.get("/{pi_id}", tags=["Research Pi"])
def get_pi(
    pi_id: int,
    current_user: dict = Depends(get_current_user),
):
    service = ResearchPiService()
    pi = service.get_by_id(pi_id)
    return {"code": 0, "data": pi, "message": "success"}


@router.post("", status_code=201, tags=["Research Pi"])
def create_pi(
    body: PiCreate,
    current_user: dict = Depends(get_current_user),
):
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="name is required")
    service = ResearchPiService()
    pi = service.create(
        name=body.name,
        institution=body.institution,
        department=body.department,
        title=body.title,
        hcp_id=body.hcp_id,
        research_areas=body.research_areas,
        total_papers=body.total_papers,
        total_grants=body.total_grants,
        h_index=body.h_index,
    )
    ResearchService().log_audit(
        event_type="create",
        entity_type="pi",
        entity_id=pi["pi_id"],
        new_value=str(pi),
        operator=current_user.get("username", ""),
    )
    return {"code": 0, "data": pi, "message": "success"}
