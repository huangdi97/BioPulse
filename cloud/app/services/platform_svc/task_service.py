"""任务服务管理任务的创建、查询与生命周期。"""

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
from shared.datetime_utils import now as _now


class TaskService(BaseService):
    def _get_board_or_404(self, board_id: int) -> dict:
        """根据 board_id 获取看板，不存在时抛出 404 异常。

        参数:
            board_id: 看板 ID

        返回:
            看板字典

        抛出:
            HTTPException: 看板不存在时抛出 404
        """
        boards_repo = TaskBoardsRepository(self._connection())
        row = boards_repo.get_active_by_id(board_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Board not found")
        return row

    def _get_task_or_404(self, board_id: int, task_id: int) -> dict:
        """根据 board_id 与 task_id 获取任务，不存在时抛出 404 异常。

        参数:
            board_id: 看板 ID
            task_id: 任务 ID

        返回:
            任务字典

        抛出:
            HTTPException: 任务不存在时抛出 404
        """
        tasks_repo = BoardTasksRepository(self._connection())
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
        """创建新任务，若指派了负责人则发送通知。

        参数:
            board_id: 所属看板 ID
            title: 任务标题
            description: 任务描述
            status_filter: 任务状态
            priority: 优先级
            assignee_id: 可选，负责人用户 ID
            due_date: 可选，截止日期
            sort_order: 排序序号
            user_id: 创建者用户 ID

        返回:
            创建完成的任务字典
        """
        self._get_board_or_404(board_id)
        tasks_repo = BoardTasksRepository(self._connection())
        notif_repo = NotificationsRepository(self._connection())
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
        """查询指定看板下的任务列表，可按状态筛选。

        参数:
            board_id: 看板 ID
            status_filter: 可选，按状态过滤

        返回:
            任务字典列表
        """
        self._get_board_or_404(board_id)
        tasks_repo = BoardTasksRepository(self._connection())
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
        """更新任务字段，仅更新提供了值的非 None 字段。

        参数:
            board_id: 看板 ID
            task_id: 任务 ID
            title: 可选，新标题
            description: 可选，新描述
            status_filter: 可选，新状态
            priority: 可选，新优先级
            assignee_id: 可选，新负责人
            due_date: 可选，新截止日期
            sort_order: 可选，新排序序号

        返回:
            更新后的任务字典
        """
        self._get_task_or_404(board_id, task_id)
        tasks_repo = BoardTasksRepository(self._connection())
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
        """软删除指定任务。

        参数:
            board_id: 看板 ID
            task_id: 待删除的任务 ID
        """
        self._get_task_or_404(board_id, task_id)
        tasks_repo = BoardTasksRepository(self._connection())
        tasks_repo.soft_delete(task_id)

    def my_tasks(self, user_id: int) -> list:
        """查询指定用户被指派的所有任务。

        参数:
            user_id: 用户 ID

        返回:
            任务字典列表
        """
        tasks_repo = BoardTasksRepository(self._connection())
        return tasks_repo.list_by_assignee(user_id)
