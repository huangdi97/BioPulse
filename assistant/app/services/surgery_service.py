import asyncio
from datetime import date, datetime, timezone
from typing import List, Optional

from assistant.app.repositories import SurgeryReminderRepository
from assistant.app.services.base import BaseService
from assistant.app.ws_manager import connection_manager
from assistant.app.reminder_scheduler import check_reminders

VALID_STATUSES = {"scheduled", "in_progress", "completed", "cancelled"}


class SurgeryService(BaseService):
    def create(self, body, user_id: int) -> dict:
        from fastapi import HTTPException
        from starlette import status

        repo = SurgeryReminderRepository(self.db)
        now = datetime.now(timezone.utc).isoformat()
        initial_status = body.status if body.status else "scheduled"
        if initial_status not in VALID_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status: {initial_status}",
            )
        row_id = repo.create(
            {
                "patient_name": body.patient_name,
                "surgery_type": body.surgery_type,
                "surgery_date": body.surgery_date,
                "hospital": body.hospital,
                "department": body.department,
                "surgeon_name": body.surgeon_name,
                "pre_op_notes": body.pre_op_notes,
                "post_op_notes": body.post_op_notes,
                "status": initial_status,
                "reminder_before": body.reminder_before if body.reminder_before is not None else 1,
                "notification_status": "pending",
                "created_by": user_id,
                "created_at": now,
                "updated_at": now,
            },
        )
        asyncio.create_task(connection_manager.send_to_user(
            user_id,
            {
                "type": "surgery_reminder",
                "title": "新手术提醒",
                "body": f"{body.patient_name} · {body.surgery_type or '手术'} · {body.hospital or ''}",
                "surgery_id": row_id,
                "surgery_date": body.surgery_date or "",
                "timestamp": now,
            },
        ))
        return {"id": row_id}

    def today(self) -> list:
        repo = SurgeryReminderRepository(self.db)
        today_str = date.today().isoformat()
        rows = repo.list_all(
            conditions=["surgery_date = ?", "is_active = 1"],
            params=[today_str],
        )
        return [dict(r) for r in rows]

    def list(
        self,
        page: int,
        page_size: int,
        patient_name: Optional[str] = None,
        surgery_status: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> tuple:
        repo = SurgeryReminderRepository(self.db)
        conditions = ["is_active = 1"]
        params: list = []
        if patient_name:
            conditions.append("patient_name LIKE ?")
            params.append(f"%{patient_name}%")
        if surgery_status:
            conditions.append("status = ?")
            params.append(surgery_status)
        if date_from:
            conditions.append("surgery_date >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("surgery_date <= ?")
            params.append(date_to)

        return repo.paginate(page, page_size, conditions, params)

    def check_reminders_now(self) -> dict:
        count = check_reminders()
        return {"triggered": count}

    def upcoming(self, page: int, page_size: int) -> tuple:
        repo = SurgeryReminderRepository(self.db)
        conditions = [
            "is_active = 1",
            "surgery_date >= date('now')",
            "surgery_date <= date('now', '+7 days')",
        ]
        return repo.paginate(page, page_size, conditions, order_by="surgery_date ASC")

    def get(self, surgery_id: int) -> dict:
        repo = SurgeryReminderRepository(self.db)
        return dict(repo.get_or_404(surgery_id))

    def update(self, surgery_id: int, body) -> dict:
        from fastapi import HTTPException
        from starlette import status

        repo = SurgeryReminderRepository(self.db)
        repo.get_or_404(surgery_id)
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(repo.get_by_id(surgery_id))
        if "status" in updates and updates["status"] not in VALID_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status: {updates['status']}",
            )
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(surgery_id, updates)
        return dict(repo.get_by_id(surgery_id))

    def delete(self, surgery_id: int) -> None:
        repo = SurgeryReminderRepository(self.db)
        repo.get_or_404(surgery_id)
        repo.soft_delete(surgery_id)
