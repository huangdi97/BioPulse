"""内容管理服务，负责内容的创建、合规检查与状态流转。"""

import json
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import ContentsRepository
from cloud.app.services.base import BaseService
from shared.base import validate_columns
from shared.columns import TABLE_CONTENTS_COLS
from shared.compliance import check_content
from shared.notification_client import send_notification

DEFAULT_RULES = [
    {"category": "prohibited_word", "keyword": "绝对安全"},
    {"category": "prohibited_word", "keyword": "无副作用"},
    {"category": "prohibited_word", "keyword": "根治"},
    {"category": "prohibited_word", "keyword": "absolutely safe"},
    {"category": "prohibited_word", "keyword": "no side effects"},
    {"category": "prohibited_word", "keyword": "cure"},
]


class ContentStatus:
    """内容状态枚举。"""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ContentService(BaseService):
    """内容服务，提供内容的增删改查与合规评分功能。"""

    def create_content(self, title: str, body: str, category: str, tags: List[str], user_id: int) -> dict:
        repo = ContentsRepository(self.db)
        tags_str = json.dumps(tags, ensure_ascii=False)

        result = check_content(body, DEFAULT_RULES)
        score = result.score
        content_status = ContentStatus.PENDING_REVIEW if score < 1.0 else ContentStatus.DRAFT
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content_id = repo.create(
            {
                "title": title,
                "body": body,
                "category": category,
                "tags": tags_str,
                "status": content_status,
                "compliance_score": score,
                "created_by": user_id,
                "created_at": now,
                "updated_at": now,
            }
        )

        if score < 1.0:
            send_notification(
                self.db,
                user_id,
                title="内容合规检查未通过",
                body=f'您的内容 "{title}" 合规评分为 {score}，已进入待审批状态。',
                category="compliance",
                ref_type="contents",
                ref_id=content_id,
            )

        row = repo.get_by_id(content_id)
        return row

    def get_content(self, content_id: int) -> dict:
        repo = ContentsRepository(self.db)
        row = repo.get_by_id(content_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Content not found")
        return row

    def list_contents(
        self,
        status_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        repo = ContentsRepository(self.db)
        conditions: List[str] = []
        params: list = []

        if status_filter:
            conditions.append("status = ?")
            params.append(status_filter)
        if category_filter:
            conditions.append("category = ?")
            params.append(category_filter)

        total, total_pages, rows = repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions or None,
            params=params or None,
            order_by="updated_at DESC",
        )
        return {
            "items": rows,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def update_content(
        self,
        content_id: int,
        title: Optional[str],
        body: Optional[str],
        category: Optional[str],
        tags: Optional[List[str]],
        status_field: Optional[str],
    ) -> dict:
        repo = ContentsRepository(self.db)
        row = repo.get_by_id(content_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Content not found")

        updates: dict = {}

        if title is not None:
            updates["title"] = title
        if body is not None:
            updates["body"] = body
            result = check_content(body, DEFAULT_RULES)
            updates["compliance_score"] = result.score
            if result.score < 1.0:
                updates["status"] = ContentStatus.PENDING_REVIEW
            elif row["status"] != ContentStatus.PENDING_REVIEW:
                updates["status"] = ContentStatus.DRAFT
        if category is not None:
            updates["category"] = category
        if tags is not None:
            updates["tags"] = json.dumps(tags, ensure_ascii=False)
        if status_field is not None:
            updates["status"] = status_field

        if updates:
            updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            validate_columns(updates, "contents", TABLE_CONTENTS_COLS)
            repo.update(content_id, updates)

        row = repo.get_by_id(content_id)
        return row

    def delete_content(self, content_id: int) -> None:
        repo = ContentsRepository(self.db)
        row = repo.get_by_id(content_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Content not found")
        if row["status"] == ContentStatus.APPROVED:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Cannot archive approved content")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        repo.update(content_id, {"status": ContentStatus.ARCHIVED, "updated_at": now})
