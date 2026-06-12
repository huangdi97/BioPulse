"""通知消息构建模块，管理模板渲染与模板 CRUD。"""

import re

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import NotificationTemplatesRepository
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


class NotificationBuilderMixin:
    """通知构建混入类，提供模板 CRUD 操作。"""

    def create_template(self, name: str, title_template: str, body_template: str, category: str) -> dict:
        tmpl_repo = NotificationTemplatesRepository(self._connection())
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
        tmpl_repo = NotificationTemplatesRepository(self._connection())
        rows = tmpl_repo.list_all(order_by="created_at DESC")
        return [_template_to_dict(r) for r in rows]

    def get_template(self, template_id: int) -> dict:
        tmpl_repo = NotificationTemplatesRepository(self._connection())
        row = tmpl_repo.get_by_id(template_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Template not found")
        return _template_to_dict(row)

    def update_template(self, template_id: int, **updates) -> dict:
        tmpl_repo = NotificationTemplatesRepository(self._connection())
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
        tmpl_repo = NotificationTemplatesRepository(self._connection())
        existing = tmpl_repo.get_by_id(template_id)
        if not existing:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Template not found")
        tmpl_repo.delete(template_id)
