from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException
from starlette import status

from sales_assistant.app.repositories import ContentRepository
from sales_assistant.app.services.base import BaseService

TYPES = [
    {"value": "product_material", "label": "产品资料"},
    {"value": "talk_track", "label": "话术模板"},
    {"value": "objection_response", "label": "异议应答"},
    {"value": "competitive_brief", "label": "竞品简报"},
    {"value": "training_tip", "label": "培训提示"},
]


class ContentService(BaseService):
    def create_content(self, body, user_id: int) -> int:
        now = datetime.now(timezone.utc).isoformat()
        repo = ContentRepository(self.db)
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
        repo = ContentRepository(self.db)
        return repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params,
            order_by="created_at DESC",
        )

    def list_content_types(self) -> list:
        return TYPES

    def get_content(self, content_id: int) -> dict:
        repo = ContentRepository(self.db)
        row = repo.get_by_id(content_id)
        if not row or row["is_active"] != 1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )
        return dict(row)

    def update_content(self, content_id: int, body) -> dict:
        repo = ContentRepository(self.db)
        row = repo.get_by_id(content_id)
        if not row or row["is_active"] != 1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(content_id, updates)
        return dict(repo.get_by_id(content_id))

    def delete_content(self, content_id: int) -> None:
        repo = ContentRepository(self.db)
        row = repo.get_by_id(content_id)
        if not row or not row["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )
        repo.soft_delete(content_id)
