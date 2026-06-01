from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException
from starlette import status

from sales_assistant.app.repositories import ScheduleRepository
from sales_assistant.app.services.base import BaseService


class ScheduleService(BaseService):
    def create_schedule(self, body, user_id: int) -> int:
        now = datetime.now(timezone.utc).isoformat()
        repo = ScheduleRepository(self.db)
        data = body.model_dump()
        data["created_by"] = user_id
        data["created_at"] = now
        data["updated_at"] = now
        return repo.create(data)

    def list_schedules(
        self,
        page: int,
        page_size: int,
        event_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> tuple:
        conditions: List[str] = []
        params: list = []
        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
        if start_date:
            conditions.append("start_time >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("start_time <= ?")
            params.append(end_date)
        repo = ScheduleRepository(self.db)
        return repo.paginate(
            page, page_size,
            conditions=conditions if conditions else None,
            params=params if params else None,
            order_by="start_time DESC",
        )

    def get_schedule(self, schedule_id: int) -> dict:
        repo = ScheduleRepository(self.db)
        row = repo.get_by_id(schedule_id)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
            )
        return dict(row)

    def update_schedule(self, schedule_id: int, body) -> dict:
        repo = ScheduleRepository(self.db)
        row = repo.get_or_404(schedule_id)
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(schedule_id, updates)
        return dict(repo.get_by_id(schedule_id))

    def delete_schedule(self, schedule_id: int) -> None:
        repo = ScheduleRepository(self.db)
        repo.get_or_404(schedule_id)
        repo.soft_delete(schedule_id)
