from typing import List, Optional

from fastapi import HTTPException
from starlette import status

from assistant.app.repositories import HcpRepository, TaskRepository
from assistant.app.services.base import BaseService


class TaskService(BaseService):
    def _check_hcp_exists(self, hcp_id: int) -> None:
        repo = HcpRepository(self.db)
        row = repo.get_by_id(hcp_id)
        if not row or row["is_active"] != 1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found"
            )

    def create_task(self, body, user_id: int) -> dict:
        if body.hcp_id is not None:
            self._check_hcp_exists(body.hcp_id)
        repo = TaskRepository(self.db)
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
        repo = TaskRepository(self.db)
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
            page=page, page_size=page_size, conditions=conditions, params=params,
        )

    def get_task(self, task_id: int) -> dict:
        repo = TaskRepository(self.db)
        row = repo.get_by_id(task_id)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )
        return dict(row)

    def update_task(self, task_id: int, body) -> dict:
        repo = TaskRepository(self.db)
        row = repo.get_by_id(task_id)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        if body.hcp_id is not None:
            self._check_hcp_exists(body.hcp_id)

        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(row)

        repo.update(task_id, updates)
        return dict(repo.get_by_id(task_id))

    def delete_task(self, task_id: int) -> None:
        repo = TaskRepository(self.db)
        row = repo.get_by_id(task_id)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )
        repo.soft_delete(task_id)
