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
    """创建知识条目。

    Args:
        body: 知识创建数据（标题、分类、内容等）
        service: 知识服务
        current_user: 当前登录用户

    Returns:
        包含新创建知识条目的 JSON 响应
    """
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
    """分页查询知识条目列表，支持按分类和难度筛选。

    Args:
        page: 页码（从1开始）
        page_size: 每页数量
        category: 分类（可选筛选）
        difficulty: 难度（可选筛选）
        service: 知识服务
        current_user: 当前登录用户

    Returns:
        分页的知识条目列表
    """
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
    """获取知识库中所有可用的分类列表。

    Args:
        service: 知识服务
        current_user: 当前登录用户

    Returns:
        分类名称列表
    """
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
    """全文搜索知识条目。

    Args:
        q: 搜索关键词
        page: 页码（从1开始）
        page_size: 每页数量
        service: 知识服务
        current_user: 当前登录用户

    Returns:
        匹配的分页知识条目列表
    """
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
    """获取指定知识条目的详细信息。

    Args:
        knowledge_id: 知识条目 ID
        service: 知识服务
        current_user: 当前登录用户

    Returns:
        知识条目详情
    """
    row = service.get(knowledge_id)
    return success(data=KnowledgeOut(**row))


@router.patch("/{knowledge_id}")
def update_knowledge(
    knowledge_id: int,
    body: KnowledgeUpdate,
    service: KnowledgeService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[KnowledgeOut]:
    """更新指定知识条目的部分字段。

    Args:
        knowledge_id: 知识条目 ID
        body: 需要更新的字段数据
        service: 知识服务
        current_user: 当前登录用户

    Returns:
        更新后的知识条目
    """
    updated = service.update(knowledge_id, body)
    return success(data=KnowledgeOut(**updated))


@router.delete("/{knowledge_id}")
def delete_knowledge(
    knowledge_id: int,
    service: KnowledgeService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """删除指定知识条目。

    Args:
        knowledge_id: 知识条目 ID
        service: 知识服务
        current_user: 当前登录用户

    Returns:
        成功删除的消息
    """
    service.delete(knowledge_id)
    return success(message="deleted")
