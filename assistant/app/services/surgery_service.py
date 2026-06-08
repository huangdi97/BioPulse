"""跟台手术服务模块。"""

import asyncio
from datetime import date, datetime, timezone
from typing import Optional

from assistant.app.reminder_scheduler import check_reminders
from assistant.app.repositories import SurgeryReminderRepository
from assistant.app.services.base import BaseCrudService
from assistant.app.ws_manager import connection_manager

VALID_STATUSES = {"scheduled", "in_progress", "completed", "cancelled"}


class SurgeryService(BaseCrudService):
    """跟台手术服务，提供手术提醒的增删改查与实时通知。"""

    def __init__(self, db=None):
        super().__init__(repository_class=SurgeryReminderRepository, entity_name="Surgery", db=db)

    def create(self, body, user_id: int) -> dict:
        """创建跟台手术提醒并通过WebSocket推送通知。

        Args:
            body: 手术提醒请求体; user_id: 用户ID

        Returns:
            dict: 包含新记录 id 的结果
        """
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
        asyncio.create_task(
            connection_manager.send_to_user(
                user_id,
                {
                    "type": "surgery_reminder",
                    "title": "新手术提醒",
                    "body": f"{body.patient_name} · {body.surgery_type or '手术'} · {body.hospital or ''}",
                    "surgery_id": row_id,
                    "surgery_date": body.surgery_date or "",
                    "timestamp": now,
                },
            )
        )
        return {"id": row_id}

    def today(self) -> list:
        """获取当日的手术列表。

        Returns:
            list: 当日手术记录列表
        """
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
        """分页查询手术提醒列表。

        Args:
            page: 页码; page_size: 每页条数; patient_name: 可选患者姓名模糊查询; surgery_status: 可选手术状态过滤; date_from: 可选起始日期过滤; date_to: 可选截止日期过滤

        Returns:
            tuple: (items, total, page, page_size, total_pages)
        """
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
        """立即触发手术提醒检查。

        Returns:
            dict: 包含 triggered（触发数量）的结果
        """
        count = check_reminders()
        return {"triggered": count}

    def upcoming(self, page: int, page_size: int) -> tuple:
        """分页查询未来7天内即将进行的手术。

        Args:
            page: 页码; page_size: 每页条数

        Returns:
            tuple: (items, total, page, page_size, total_pages)
        """
        repo = SurgeryReminderRepository(self.db)
        conditions = [
            "is_active = 1",
            "surgery_date >= date('now')",
            "surgery_date <= date('now', '+7 days')",
        ]
        return repo.paginate(page, page_size, conditions, order_by="surgery_date ASC")

    def get(self, surgery_id: int) -> dict:
        """根据ID获取手术提醒详情。

        Args:
            surgery_id: 手术提醒ID

        Returns:
            dict: 手术提醒记录详情
        """
        repo = SurgeryReminderRepository(self.db)
        return dict(repo.get_or_404(surgery_id))

    def update(self, surgery_id: int, body) -> dict:
        """更新手术提醒记录。

        Args:
            surgery_id: 手术提醒ID; body: 更新数据请求体

        Returns:
            dict: 更新后的手术提醒记录
        """
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
        """软删除手术提醒记录。

        Args:
            surgery_id: 手术提醒ID
        """
        repo = SurgeryReminderRepository(self.db)
        repo.get_or_404(surgery_id)
        repo.soft_delete(surgery_id)
