"""科研轨迹查询 API。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette import status

from opportunity.app.services.research_service import ResearchService
from shared.auth_scope import require_scope
from shared.base import ApiResponse, PaginatedResponse, success

router = APIRouter(prefix="/research-trails", tags=["research"])


class ResearchTrailCreate(BaseModel):
    hcp_name: str
    topic: str
    paper_title: Optional[str] = None
    authors: Optional[str] = None
    journal: Optional[str] = None
    pub_date: Optional[str] = None
    pubmed_id: Optional[str] = None
    url: Optional[str] = None
    summary: Optional[str] = None
    relevance: Optional[int] = Field(default=5, ge=1, le=10)


class ResearchTrailUpdate(BaseModel):
    hcp_name: Optional[str] = None
    topic: Optional[str] = None
    paper_title: Optional[str] = None
    authors: Optional[str] = None
    journal: Optional[str] = None
    pub_date: Optional[str] = None
    pubmed_id: Optional[str] = None
    url: Optional[str] = None
    summary: Optional[str] = None
    relevance: Optional[int] = Field(default=None, ge=1, le=10)
    is_active: Optional[int] = None


class ResearchTrailOut(BaseModel):
    id: int
    hcp_name: str
    topic: str
    paper_title: Optional[str] = None
    authors: Optional[str] = None
    journal: Optional[str] = None
    pub_date: Optional[str] = None
    pubmed_id: Optional[str] = None
    url: Optional[str] = None
    summary: Optional[str] = None
    relevance: int = 5
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("", summary="创建轨迹", description="创建新的科研轨迹记录")
def create_research_trail(
    body: ResearchTrailCreate,
    service: ResearchService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> JSONResponse:
    """创建research trail。"""
    user_id = int(current_user["sub"])
    new_id = service.create_research_trail(body, user_id)
    return JSONResponse(
        content=success(data={"id": new_id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("", summary="轨迹列表", description="分页查询科研轨迹，支持按医生、主题等筛选")
def list_research_trails(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    hcp_name: Optional[str] = Query(None),
    topic: Optional[str] = Query(None),
    journal: Optional[str] = Query(None),
    relevance_min: Optional[int] = Query(None),
    service: ResearchService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[PaginatedResponse[ResearchTrailOut]]:
    """获取research trails。"""
    total, total_pages, rows = service.list_research_trails(
        page=page,
        page_size=page_size,
        hcp_name=hcp_name,
        topic=topic,
        journal=journal,
        relevance_min=relevance_min,
    )
    items = [ResearchTrailOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/{trail_id}", summary="轨迹详情", description="获取指定科研轨迹的详细信息")
def get_research_trail(
    trail_id: int,
    service: ResearchService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[ResearchTrailOut]:
    """获取research trail。"""
    row = service.get_research_trail(trail_id)
    return success(data=ResearchTrailOut(**row))


@router.patch("/{trail_id}", summary="更新轨迹", description="更新指定科研轨迹的信息")
def update_research_trail(
    trail_id: int,
    body: ResearchTrailUpdate,
    service: ResearchService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[ResearchTrailOut]:
    """更新research trail。"""
    updated = service.update_research_trail(trail_id, body)
    return success(data=ResearchTrailOut(**updated))


@router.delete("/{trail_id}", summary="删除轨迹", description="删除指定的科研轨迹记录")
def delete_research_trail(
    trail_id: int,
    service: ResearchService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """删除research trail。"""
    service.delete_research_trail(trail_id)
    return success(message="deleted")
