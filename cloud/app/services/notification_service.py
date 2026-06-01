import json
import re
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    NotificationsRepository,
    NotificationTemplatesRepository,
)
from cloud.app.services.base import BaseService
from shared.base import validate_columns
from shared.columns import TABLE_NOTIFICATION_TEMPLATES_COLS


def _render_template(template: str, context: dict) -> str:
    def replacer(match):
        key = match.group(1)
        return str(context.get(key, match.group(0)))

    return re.sub(r"\{(\w+)\}", replacer, template)


def _template_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "title_template": row["title_template"],
        "body_template": row["body_template"],
        "category": row["category"],
        "created_at": row["created_at"],
    }


def _notification_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "template_id": row["template_id"],
        "title": row["title"],
        "body": row["body"],
        "category": row["category"],
        "ref_type": row["ref_type"],
        "ref_id": row["ref_id"],
        "context_json": row["context_json"],
        "is_read": row["is_read"],
        "read_at": row["read_at"],
        "created_at": row["created_at"],
    }


class NotificationService(BaseService):
    def create_template(self, name: str, title_template: str, body_template: str, category: str) -> dict:
        tmpl_repo = NotificationTemplatesRepository(self.db)
        row_id = tmpl_repo.create(
            {
                "name": name,
                "title_template": title_template,
                "body_template": body_template,
                "category": category,
            }
        )
        row = tmpl_repo.get_by_id(row_id)
        return _template_to_dict(row)

    def list_templates(self) -> list:
        tmpl_repo = NotificationTemplatesRepository(self.db)
        rows = tmpl_repo.list_all(order_by="created_at DESC")
        return [_template_to_dict(r) for r in rows]

    def get_template(self, template_id: int) -> dict:
        tmpl_repo = NotificationTemplatesRepository(self.db)
        row = tmpl_repo.get_by_id(template_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Template not found")
        return _template_to_dict(row)

    def update_template(self, template_id: int, **updates) -> dict:
        tmpl_repo = NotificationTemplatesRepository(self.db)
        existing = tmpl_repo.get_by_id(template_id)
        if not existing:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Template not found")
        filtered = {}
        for field in ("name", "title_template", "body_template", "category"):
            val = updates.get(field)
            if val is not None:
                filtered[field] = val
        if filtered:
            validate_columns(filtered, "notification_templates", TABLE_NOTIFICATION_TEMPLATES_COLS)
            tmpl_repo.update(template_id, filtered)
        row = tmpl_repo.get_by_id(template_id)
        return _template_to_dict(row)

    def delete_template(self, template_id: int) -> None:
        tmpl_repo = NotificationTemplatesRepository(self.db)
        existing = tmpl_repo.get_by_id(template_id)
        if not existing:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Template not found")
        tmpl_repo.delete(template_id)

    def send(
        self,
        user_id: int,
        template_name: Optional[str] = None,
        title: Optional[str] = None,
        body: Optional[str] = None,
        category: Optional[str] = None,
        context: Optional[dict] = None,
        ref_type: Optional[str] = None,
        ref_id: Optional[int] = None,
    ) -> dict:
        title = title
        body_text = body
        category = category
        template_id = None
        context_json = ""
        db = self.db

        if template_name:
            tmpl_repo = NotificationTemplatesRepository(db)
            placeholders = ", ".join(tmpl_repo.cols)
            template = db.execute(
                f"SELECT {placeholders} FROM {tmpl_repo.table_name} WHERE name=?",
                (template_name,),
            ).fetchone()
            if not template:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Template not found")
            ctx = context or {}
            title = _render_template(template["title_template"], ctx)
            body_text = _render_template(template["body_template"], ctx)
            category = category or template["category"]
            template_id = template["id"]
            context_json = json.dumps(ctx, ensure_ascii=False)

        if not title or not body_text or not category:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="title, body, and category are required (or provide template_name + context)",
            )

        notif_repo = NotificationsRepository(db)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row_id = notif_repo.create(
            {
                "user_id": user_id,
                "template_id": template_id,
                "title": title,
                "body": body_text,
                "category": category,
                "ref_type": ref_type or "",
                "ref_id": ref_id,
                "context_json": context_json,
                "created_at": now,
            }
        )
        row = notif_repo.get_by_id(row_id)
        return _notification_to_dict(row)

    def list_notifications(
        self,
        user_id: int,
        is_read: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        conditions = ["user_id=?"]
        params = [user_id]
        if is_read is not None:
            conditions.append("is_read=?")
            params.append(is_read)

        notif_repo = NotificationsRepository(self.db)
        total, _, items = notif_repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params,
            order_by="created_at DESC",
        )
        return {
            "items": [_notification_to_dict(r) for r in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def mark_read(self, notification_id: int, user_id: int) -> dict:
        notif_repo = NotificationsRepository(self.db)
        db = self.db
        placeholders = ", ".join(notif_repo.cols)
        row = db.execute(
            f"SELECT {placeholders} FROM {notif_repo.table_name} WHERE id=? AND user_id=?",
            (notification_id, user_id),
        ).fetchone()
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Notification not found")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        notif_repo.update(notification_id, {"is_read": 1, "read_at": now})
        row = notif_repo.get_by_id(notification_id)
        return _notification_to_dict(row)

    def unread_count(self, user_id: int) -> dict:
        notif_repo = NotificationsRepository(self.db)
        count = notif_repo.count(conditions=["user_id=?", "is_read=0"], params=[user_id])
        return {"count": count}
