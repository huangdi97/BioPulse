"""日程服务：销售日程的创建、查询、更新与删除。"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException
from starlette import status

from sales_assistant.app.repositories import ScheduleRepository
from sales_assistant.app.services.base import BaseCrudService


class ScheduleService(BaseCrudService):
    """日程服务：管理销售代表的工作日程与事件。"""

    _repo_class = ScheduleRepository
    _entity_name = "Schedule"

    def create_schedule(self, body, user_id: int) -> int:
        """创建日程事件。

        Args:
            body: 日程请求体。
            user_id: 创建者用户ID。

        Returns:
            新创建的日程ID。
        """
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
        """分页查询日程列表。

        Args:
            page: 页码。
            page_size: 每页条数。
            event_type: 按事件类型筛选。
            start_date: 开始时间下限。
            end_date: 开始时间上限。

        Returns:
            (记录列表, 总条数) 元组。
        """
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
            page,
            page_size,
            conditions=conditions if conditions else None,
            params=params if params else None,
            order_by="start_time DESC",
        )

    def get_schedule(self, schedule_id: int) -> dict:
        """获取单个日程详情。

        Args:
            schedule_id: 日程ID。

        Returns:
            日程详情字典，不存在则抛404。
        """
        repo = ScheduleRepository(self.db)
        row = repo.get_by_id(schedule_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
        return dict(row)

    def update_schedule(self, schedule_id: int, body) -> dict:
        """更新日程。

        Args:
            schedule_id: 日程ID。
            body: 更新数据。

        Returns:
            更新后的日程详情。
        """
        repo = ScheduleRepository(self.db)
        row = repo.get_or_404(schedule_id)
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(schedule_id, updates)
        return dict(repo.get_by_id(schedule_id))

    def delete_schedule(self, schedule_id: int) -> None:
        """软删除日程。

        Args:
            schedule_id: 日程ID。
        """
        repo = ScheduleRepository(self.db)
        repo.get_or_404(schedule_id)
        repo.soft_delete(schedule_id)
