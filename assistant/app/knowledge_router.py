from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette import status

from assistant.app.services.knowledge_service import KnowledgeService
from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class KnowledgeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    category: Optional[str] = None
    content: str
    tags: Optional[str] = None
    source: Optional[str] = None
    difficulty: Optional[str] = None


class KnowledgeUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    source: Optional[str] = None
    difficulty: Optional[str] = None


class KnowledgeOut(BaseModel):
    id: int
    title: str
    category: Optional[str] = None
    content: str
    tags: Optional[str] = None
    source: Optional[str] = None
    difficulty: Optional[str] = None
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("")
def create_knowledge(
    body: KnowledgeCreate,
    service: KnowledgeService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    user_id = int(current_user["sub"])
    result = service.create(body, user_id)
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("")
def list_knowledge(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    service: KnowledgeService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[KnowledgeOut]]:
    total, total_pages, rows = service.list(page, page_size, category, difficulty)
    items = [KnowledgeOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/categories")
def list_categories(
    service: KnowledgeService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[List[str]]:
    categories = service.list_categories()
    return success(data=categories)


@router.get("/search")
def search_knowledge(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: KnowledgeService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[KnowledgeOut]]:
    total, total_pages, rows = service.search(q, page, page_size)
    items = [KnowledgeOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/{knowledge_id}")
def get_knowledge(
    knowledge_id: int,
    service: KnowledgeService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[KnowledgeOut]:
    row = service.get(knowledge_id)
    return success(data=KnowledgeOut(**row))


@router.patch("/{knowledge_id}")
def update_knowledge(
    knowledge_id: int,
    body: KnowledgeUpdate,
    service: KnowledgeService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[KnowledgeOut]:
    updated = service.update(knowledge_id, body)
    return success(data=KnowledgeOut(**updated))


@router.delete("/{knowledge_id}")
def delete_knowledge(
    knowledge_id: int,
    service: KnowledgeService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    service.delete(knowledge_id)
    return success(message="deleted")
