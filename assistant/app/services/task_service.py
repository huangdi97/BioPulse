"""任务管理服务模块。"""

from typing import List, Optional

from fastapi import HTTPException
from starlette import status

from assistant.app.repositories import HcpRepository, TaskRepository
from shared.base_service import BaseCrudService


class TaskService(BaseCrudService):
    """任务管理服务，提供任务的增删改查，关联HCP校验。"""

    def __init__(self, db=None):
        super().__init__(repository_class=TaskRepository, entity_name="Task", db=db)

    def _check_hcp_exists(self, hcp_id: int) -> None:
        repo = HcpRepository(self._connection())
        row = repo.get_by_id(hcp_id)
        if not row or row["is_active"] != 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")

    def create_task(self, body, user_id: int) -> dict:
        """创建任务，若关联HCP则校验HCP是否存在。

        Args:
            body: 任务请求体; user_id: 用户ID

        Returns:
            dict: 包含新任务 id 的结果
        """
        if body.hcp_id is not None:
            self._check_hcp_exists(body.hcp_id)
        repo = TaskRepository(self._connection())
        row_id = repo.create(
            body.model_dump(),
            extra={"created_by": user_id},
        )
        return {"id": row_id}

    def list_tasks(
        self,
        page: int,
        page_size: int,
        hcp_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> tuple:
        """分页查询任务列表。

        Args:
            page: 页码; page_size: 每页条数; hcp_id: 可选HCP ID过滤; status_filter: 可选状态过滤; priority: 可选优先级过滤

        Returns:
            tuple: (items, total, page, page_size, total_pages)
        """
        repo = TaskRepository(self._connection())
        conditions: List[str] = []
        params: list = []

        if hcp_id is not None:
            conditions.append("hcp_id = ?")
            params.append(hcp_id)
        if status_filter:
            conditions.append("status = ?")
            params.append(status_filter)
        if priority:
            conditions.append("priority = ?")
            params.append(priority)

        return repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions,
            params=params,
        )

    def get_task(self, task_id: int) -> dict:
        """根据ID获取任务详情。

        Args:
            task_id: 任务ID

        Returns:
            dict: 任务记录详情
        """
        repo = TaskRepository(self._connection())
        row = repo.get_by_id(task_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        return dict(row)

    def update_task(self, task_id: int, body) -> dict:
        """更新任务记录。

        Args:
            task_id: 任务ID; body: 更新数据请求体

        Returns:
            dict: 更新后的任务记录
        """
        repo = TaskRepository(self._connection())
        row = repo.get_by_id(task_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        if body.hcp_id is not None:
            self._check_hcp_exists(body.hcp_id)

        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)

        repo.update(task_id, updates)
        return dict(repo.get_by_id(task_id))

    def delete_task(self, task_id: int) -> None:
        """软删除任务记录。

        Args:
            task_id: 任务ID
        """
        repo = TaskRepository(self._connection())
        row = repo.get_by_id(task_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        repo.soft_delete(task_id)
