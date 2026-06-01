import sqlite3
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from starlette import status

from opportunity.app.repositories import UserBookmarkRepository
from opportunity.app.services.base import BaseService


class BookmarkService(BaseService):
    def create_bookmark(self, body, user_id: int) -> int:
        repo = UserBookmarkRepository(self.db)
        now = datetime.now(timezone.utc).isoformat()
        try:
            return repo.create(body.model_dump(), extra={
                "created_by": user_id,
                "created_at": now,
            })
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bookmark already exists",
            )

    def list_bookmarks(
        self, page: int, page_size: int, user_id: int, entity_type: Optional[str] = None
    ) -> tuple:
        conditions = ["created_by = ?"]
        params: list = [user_id]
        if entity_type:
            conditions.append("entity_type = ?")
            params.append(entity_type)
        repo = UserBookmarkRepository(self.db)
        return repo.paginate(
            page, page_size,
            conditions=conditions,
            params=params,
            order_by="created_at DESC",
        )

    def check_bookmark(self, entity_type: str, entity_id: int, user_id: int) -> Optional[dict]:
        repo = UserBookmarkRepository(self.db)
        row = repo.get_by_entity(entity_type, entity_id, user_id)
        return dict(row) if row else None

    def delete_bookmark(self, bookmark_id: int, user_id: int) -> None:
        repo = UserBookmarkRepository(self.db)
        row = repo.get_by_id(bookmark_id)
        if not row or row["created_by"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bookmark not found",
            )
        repo.soft_delete(bookmark_id)
