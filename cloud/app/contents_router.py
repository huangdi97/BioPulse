from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from shared.auth_scope import require_scope
from shared.base import success
from cloud.app.services.content_service import ContentService


router = APIRouter(prefix="/contents", tags=["contents"])


class ContentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)
    category: str
    tags: List[str] = []


class ContentResponse(BaseModel):
    id: int
    title: str
    body: str
    category: str
    tags: str
    status: str
    compliance_score: Optional[float] = None
    created_by: int
    created_at: str
    updated_at: str


class ContentUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


class PaginatedContents(BaseModel):
    items: List[ContentResponse]
    total: int
    page: int
    page_size: int


@router.post("/")
def create_content(
    body: ContentCreate,
    current_user: dict = Depends(require_scope("visit")),
    service: ContentService = Depends(),
) -> Any:
    user_id = int(current_user["sub"])
    row = service.create_content(
        body.title, body.body, body.category, body.tags, user_id
    )
    return success(data=row)


@router.get("/")
def list_contents(
    status_param: str = Query(None, alias="status"),
    category: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_scope("visit")),
    service: ContentService = Depends(),
) -> Any:
    result = service.list_contents(
        status_filter=status_param,
        category_filter=category,
        page=page,
        page_size=page_size,
    )
    return success(data=result)


@router.get("/{content_id:int}")
def get_content(
    content_id: int,
    current_user: dict = Depends(require_scope("visit")),
    service: ContentService = Depends(),
) -> Any:
    row = service.get_content(content_id)
    return success(data=row)


@router.patch("/{content_id:int}")
def update_content(
    content_id: int,
    body: ContentUpdate,
    current_user: dict = Depends(require_scope("visit")),
    service: ContentService = Depends(),
) -> Any:
    row = service.update_content(
        content_id,
        title=body.title,
        body=body.body,
        category=body.category,
        tags=body.tags,
        status_field=body.status,
    )
    return success(data=row)


@router.delete("/{content_id:int}")
def delete_content(
    content_id: int,
    current_user: dict = Depends(require_scope("visit")),
    service: ContentService = Depends(),
) -> Any:
    service.delete_content(content_id)
    return success()
