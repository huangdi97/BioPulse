"""任务服务管理任务的创建、查询与生命周期。"""

from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    BoardTasksRepository,
    NotificationsRepository,
    TaskBoardsRepository,
)
from shared.base import validate_columns
from shared.base_service import BaseService
from shared.columns import TABLE_BOARD_TASKS_COLS


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class TaskService(BaseService):
    def _get_board_or_404(self, board_id: int) -> dict:
        boards_repo = TaskBoardsRepository(self.db)
        row = boards_repo.get_active_by_id(board_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Board not found")
        return row

    def _get_task_or_404(self, board_id: int, task_id: int) -> dict:
        tasks_repo = BoardTasksRepository(self.db)
        row = tasks_repo.get_by_board_and_id(board_id, task_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
        return row

    def create_task(
        self,
        board_id: int,
        title: str,
        description: str,
        status_filter: str,
        priority: str,
        assignee_id: Optional[int],
        due_date: Optional[str],
        sort_order: int,
        user_id: int,
    ) -> dict:
        self._get_board_or_404(board_id)
        tasks_repo = BoardTasksRepository(self.db)
        notif_repo = NotificationsRepository(self.db)
        now = _now()
        task_id = tasks_repo.create(
            {
                "board_id": board_id,
                "title": title,
                "description": description,
                "status": status_filter,
                "priority": priority,
                "assignee_id": assignee_id,
                "due_date": due_date,
                "sort_order": sort_order,
                "created_by": user_id,
                "created_at": now,
                "updated_at": now,
            }
        )
        if assignee_id is not None:
            notif_repo.create_notification(
                user_id=assignee_id,
                title="新任务指派",
                body_text=f"你被指派了任务：{title}",
                category="task",
                ref_type="board_tasks",
                ref_id=task_id,
            )
        return tasks_repo.get_by_id(task_id)

    def list_tasks(self, board_id: int, status_filter: Optional[str] = None) -> list:
        self._get_board_or_404(board_id)
        tasks_repo = BoardTasksRepository(self.db)
        return tasks_repo.list_by_board(board_id, status_filter=status_filter)

    def update_task(
        self,
        board_id: int,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status_filter: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[int] = None,
        due_date: Optional[str] = None,
        sort_order: Optional[int] = None,
    ) -> dict:
        self._get_task_or_404(board_id, task_id)
        tasks_repo = BoardTasksRepository(self.db)
        updates = {}
        if title is not None:
            updates["title"] = title
        if description is not None:
            updates["description"] = description
        if status_filter is not None:
            updates["status"] = status_filter
        if priority is not None:
            updates["priority"] = priority
        if assignee_id is not None:
            updates["assignee_id"] = assignee_id
        if due_date is not None:
            updates["due_date"] = due_date
        if sort_order is not None:
            updates["sort_order"] = sort_order
        if updates:
            updates["updated_at"] = _now()
            validate_columns(updates, "board_tasks", TABLE_BOARD_TASKS_COLS)
            tasks_repo.update(task_id, updates)
        return tasks_repo.get_by_board_and_id(board_id, task_id)

    def delete_task(self, board_id: int, task_id: int) -> None:
        self._get_task_or_404(board_id, task_id)
        tasks_repo = BoardTasksRepository(self.db)
        tasks_repo.soft_delete(task_id)

    def my_tasks(self, user_id: int) -> list:
        tasks_repo = BoardTasksRepository(self.db)
        return tasks_repo.list_by_assignee(user_id)
