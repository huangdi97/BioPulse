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
        self._check_schedule_exists(schedule_id)
        repo = NoteRepository(self.db)
        return repo.paginate(
            page=page,
            page_size=page_size,
            conditions=["schedule_id = ?"],
            params=[schedule_id],
        )

    def get_note(self, note_id: int) -> dict:
        repo = NoteRepository(self.db)
        row = repo.get_by_id(note_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
        return dict(row)

    def update_note(self, note_id: int, body) -> dict:
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
        repo = NoteRepository(self.db)
        repo.get_or_404(note_id)
        repo.soft_delete(note_id)
