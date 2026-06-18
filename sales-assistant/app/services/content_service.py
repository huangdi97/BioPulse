"""内容服务：销售材料、话术模板、异议应答等内容管理。"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException
from starlette import status

from sales_assistant.app.repositories import ContentRepository
from shared.base_service import BaseCrudService

TYPES = [
    {"value": "product_material", "label": "产品资料"},
    {"value": "talk_track", "label": "话术模板"},
    {"value": "objection_response", "label": "异议应答"},
    {"value": "competitive_brief", "label": "竞品简报"},
    {"value": "training_tip", "label": "培训提示"},
]


class ContentService(BaseCrudService):
    """内容服务：管理内容库的增删改查与分类。"""

    _repo_class = ContentRepository
    _entity_name = "Content"

    def create_content(self, body, user_id: int) -> int:
        """创建内容条目。

        Args:
            body: 内容请求体。
            user_id: 创建者用户ID。

        Returns:
            新创建的内容ID。
        """
        now = datetime.now(timezone.utc).isoformat()
        repo = ContentRepository(self._connection())
        return repo.create(
            body.model_dump(),
            extra={"created_by": user_id, "created_at": now, "updated_at": now},
        )

    def list_contents(
        self,
        page: int,
        page_size: int,
        content_type: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        q: Optional[str] = None,
    ) -> tuple:
        """分页查询内容列表，支持多条件筛选和关键词搜索。

        Args:
            page: 页码。
            page_size: 每页条数。
            content_type: 按内容类型筛选。
            category: 按分类筛选。
            tag: 按标签筛选。
            q: 关键词搜索（匹配标题、摘要、标签）。

        Returns:
            (记录列表, 总条数) 元组。
        """
        conditions: List[str] = ["is_active = 1"]
        params: list = []
        if content_type:
            conditions.append("content_type = ?")
            params.append(content_type)
        if category:
            conditions.append("category LIKE ?")
            params.append(f"%{category}%")
        if tag:
            conditions.append("tags LIKE ?")
            params.append(f"%{tag}%")
        if q:
            conditions.append("(title LIKE ? OR summary LIKE ? OR tags LIKE ?)")
            like_q = f"%{q}%"
            params.extend([like_q, like_q, like_q])
        repo = ContentRepository(self._connection())
        return repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params,
            order_by="created_at DESC",
        )

    def list_content_types(self) -> list:
        """获取所有支持的内容类型列表。

        Returns:
            内容类型列表，每个元素含 value 和 label。
        """
        return TYPES

    def get_content(self, content_id: int) -> dict:
        """获取单个内容详情。

        Args:
            content_id: 内容ID。

        Returns:
            内容详情字典，不存在或已删除则抛404。
        """
        repo = ContentRepository(self._connection())
        row = repo.get_by_id(content_id)
        if not row or row["is_active"] != 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
        return dict(row)

    def update_content(self, content_id: int, body) -> dict:
        """更新内容。

        Args:
            content_id: 内容ID。
            body: 更新数据。

        Returns:
            更新后的内容详情。
        """
        repo = ContentRepository(self._connection())
        row = repo.get_by_id(content_id)
        if not row or row["is_active"] != 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(content_id, updates)
        return dict(repo.get_by_id(content_id))

    def delete_content(self, content_id: int) -> None:
        """软删除内容。

        Args:
            content_id: 内容ID。
        """
        repo = ContentRepository(self._connection())
        row = repo.get_by_id(content_id)
        if not row or not row["is_active"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
        repo.soft_delete(content_id)
