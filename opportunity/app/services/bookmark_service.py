"""书签服务，用于管理用户收藏的标书和商机信息。"""

import sqlite3
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from starlette import status

from opportunity.app.repositories import UserBookmarkRepository
from shared.base_service import BaseCrudService

"""收藏管理服务，提供用户收藏的创建、查询与删除。"""


class BookmarkService(BaseCrudService):
    """用户收藏管理：添加收藏（防重复）、分页列表、检查是否已收藏、软删除。"""

    def __init__(self, db=None):
        super().__init__(repository_class=UserBookmarkRepository, entity_name="Bookmark", db=db)

    def create_bookmark(self, body, user_id: int) -> int:
        """添加用户收藏，重复收藏会返回冲突错误。

        Args:
            body: 收藏请求体; user_id: 用户ID

        Returns:
            int: 新收藏记录ID
        """
        repo = UserBookmarkRepository(self.db)
        now = datetime.now(timezone.utc).isoformat()
        try:
            return repo.create(
                body.model_dump(),
                extra={
                    "created_by": user_id,
                    "created_at": now,
                },
            )
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bookmark already exists",
            )

    def list_bookmarks(self, page: int, page_size: int, user_id: int, entity_type: Optional[str] = None) -> tuple:
        """分页查询用户收藏列表。

        Args:
            page: 页码; page_size: 每页条数; user_id: 用户ID; entity_type: 可选实体类型过滤

        Returns:
            tuple: (items, total, page, page_size, total_pages)
        """
        conditions = ["created_by = ?"]
        params: list = [user_id]
        if entity_type:
            conditions.append("entity_type = ?")
            params.append(entity_type)
        repo = UserBookmarkRepository(self.db)
        return repo.paginate(
            page,
            page_size,
            conditions=conditions,
            params=params,
            order_by="created_at DESC",
        )

    def check_bookmark(self, entity_type: str, entity_id: int, user_id: int) -> Optional[dict]:
        """检查用户是否已收藏指定实体。

        Args:
            entity_type: 实体类型; entity_id: 实体ID; user_id: 用户ID

        Returns:
            Optional[dict]: 已收藏时返回收藏记录，否则返回 None
        """
        repo = UserBookmarkRepository(self.db)
        row = repo.get_by_entity(entity_type, entity_id, user_id)
        return dict(row) if row else None

    def delete_bookmark(self, bookmark_id: int, user_id: int) -> None:
        """软删除用户收藏。

        Args:
            bookmark_id: 收藏记录ID; user_id: 用户ID（校验所有权）
        """
        repo = UserBookmarkRepository(self.db)
        row = repo.get_by_id(bookmark_id)
        if not row or row["created_by"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bookmark not found",
            )
        repo.soft_delete(bookmark_id)
