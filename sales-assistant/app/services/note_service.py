"""拜访笔记服务：日程关联笔记的创建、查阅与管理。"""

from datetime import datetime, timezone

from fastapi import HTTPException
from starlette import status

from sales_assistant.app.repositories import NoteRepository
from sales_assistant.app.services.base import BaseService


class NoteService(BaseService):
    """拜访笔记服务：为日程记录拜访笔记，支持增删改查。"""

    def _check_schedule_exists(self, schedule_id: int) -> None:
        row = self.db.execute("SELECT id FROM schedule WHERE id = ?", (schedule_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")

    def create_note(self, schedule_id: int, body, user_id: int) -> int:
        """为指定日程创建拜访笔记。

        Args:
            schedule_id: 日程ID。
            body: 笔记请求体，含标题、内容、参与人等。
            user_id: 创建者用户ID。

        Returns:
            新创建的笔记ID。
        """
        self._check_schedule_exists(schedule_id)
        now = datetime.now(timezone.utc).isoformat()
        repo = NoteRepository(self.db)
        return repo.create(
            {
                "schedule_id": schedule_id,
                "title": body.title,
                "content": body.content,
                "participants": body.participants,
                "action_items": body.action_items,
                "created_by": user_id,
                "created_at": now,
                "updated_at": now,
            }
        )

    def list_notes(self, schedule_id: int, page: int, page_size: int) -> tuple:
        """分页查询指定日程的笔记列表。

        Args:
            schedule_id: 日程ID。
            page: 页码。
            page_size: 每页条数。

        Returns:
            (记录列表, 总条数) 元组。
        """
        self._check_schedule_exists(schedule_id)
        repo = NoteRepository(self.db)
        return repo.paginate(
            page=page,
            page_size=page_size,
            conditions=["schedule_id = ?"],
            params=[schedule_id],
        )

    def get_note(self, note_id: int) -> dict:
        """获取单个笔记详情。

        Args:
            note_id: 笔记ID。

        Returns:
            笔记详情字典，不存在则抛404。
        """
        repo = NoteRepository(self.db)
        row = repo.get_by_id(note_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
        return dict(row)

    def update_note(self, note_id: int, body) -> dict:
        """更新笔记。

        Args:
            note_id: 笔记ID。
            body: 更新数据。

        Returns:
            更新后的笔记详情。
        """
        repo = NoteRepository(self.db)
        row = repo.get_by_id(note_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(note_id, updates)
        return dict(repo.get_by_id(note_id))

    def delete_note(self, note_id: int) -> None:
        """软删除笔记。

        Args:
            note_id: 笔记ID。
        """
        repo = NoteRepository(self.db)
        repo.get_or_404(note_id)
        repo.soft_delete(note_id)
