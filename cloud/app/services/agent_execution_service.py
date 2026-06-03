import json
import uuid
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import AgentExecutionTasksRepository, AgentSkillsRepository
from cloud.app.services.base import BaseService
from shared.base import success


def _row(r):
    if not r:
        return None
    d = dict(r)
    for k in ("input_data", "output_data"):
        if k in d and isinstance(d[k], str):
            try:
                d[k] = json.loads(d[k])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


def _rows(rows):
    return [_row(r) for r in rows]


class AgentExecutionService(BaseService):
    """AgentExecution 服务类。"""

    def submit_task(self, agent_role: str, action_type: str, input_data: dict, max_retries: int) -> dict:
        """submit_task 操作。

        Args:
            agent_role: 描述
            action_type: 描述
            input_data: 描述
            max_retries: 描述

        Returns:
            描述
        """
        repo = AgentExecutionTasksRepository(self.db)
        task_id = f"aet:{uuid.uuid4()}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        repo.create(
            {
                "task_id": task_id,
                "source": "internal",
                "agent_role": agent_role,
                "action_type": action_type,
                "input_data": json.dumps(input_data, ensure_ascii=False),
                "max_retries": max_retries,
                "status": "completed",
                "created_at": now,
                "completed_at": now,
                "duration_ms": 0,
            }
        )
        row = repo.get_by_task_id(task_id)
        return success(data=_row(row))

    def list_tasks(self, status_filter: Optional[str] = None, agent_role: Optional[str] = None) -> dict:
        """获取任务列表。

        Args:
            status_filter: 描述
            agent_role: 描述

        Returns:
            描述
        """
        repo = AgentExecutionTasksRepository(self.db)
        conds, pars = [], []
        if status_filter:
            conds.append("status=?")
            pars.append(status_filter)
        if agent_role:
            conds.append("agent_role=?")
            pars.append(agent_role)
        rows = repo.list_all(conditions=conds or None, params=pars or None, order_by="created_at DESC")
        return success(data=_rows(rows))

    def get_task(self, task_id: str) -> dict:
        """获取任务。

        Args:
            task_id: 描述

        Returns:
            描述
        """
        repo = AgentExecutionTasksRepository(self.db)
        row = repo.get_by_task_id(task_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
        return success(data=_row(row))

    def retry_task(self, task_id: str) -> dict:
        """retry_task 操作。

        Args:
            task_id: 描述

        Returns:
            描述
        """
        repo = AgentExecutionTasksRepository(self.db)
        row = repo.get_by_task_id(task_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
        new_count = row["retry_count"] + 1
        repo.update(row["id"], {"retry_count": new_count, "status": "pending"})
        updated = repo.get_by_task_id(task_id)
        return success(data=_row(updated))

    def approve_task(self, task_id: str) -> dict:
        """approve_task 操作。

        Args:
            task_id: 描述

        Returns:
            描述
        """
        repo = AgentExecutionTasksRepository(self.db)
        row = repo.get_by_task_id(task_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        repo.update(row["id"], {"status": "completed", "completed_at": now})
        updated = repo.get_by_task_id(task_id)
        return success(data=_row(updated))

    def a2a_card(self) -> dict:
        """a2a_card 操作。

        Returns:
            描述
        """
        skills_repo = AgentSkillsRepository(self.db)
        rows = skills_repo.list_all(conditions=["enabled=1"], order_by="priority ASC")
        skill_names = [s["skill_name"] for s in rows]
        return success(data={"name": "Cloud Agent", "skills": skill_names})

    def a2a_task(self, task_id: str, agent_role: str, input_data: dict, callback_url: str) -> dict:
        """a2a_task 操作。

        Args:
            task_id: 描述
            agent_role: 描述
            input_data: 描述
            callback_url: 描述

        Returns:
            描述
        """
        repo = AgentExecutionTasksRepository(self.db)
        tid = task_id or f"aet:{uuid.uuid4()}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        repo.create(
            {
                "task_id": tid,
                "source": "a2a",
                "agent_role": agent_role,
                "action_type": "process",
                "input_data": json.dumps(input_data, ensure_ascii=False),
                "status": "pending",
                "created_at": now,
            }
        )
        row = repo.get_by_task_id(tid)
        return success(data=_row(row))
