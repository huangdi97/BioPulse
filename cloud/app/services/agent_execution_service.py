"""Agent 执行任务服务，管理自身数据库连接与仓库。"""

import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import AgentExecutionTasksRepository, AgentSkillsRepository

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "cloud.db")

logger = logging.getLogger(__name__)


class AgentExecutionService:
    @staticmethod
    def _conn():
        c = sqlite3.connect(DB_PATH)
        c.row_factory = sqlite3.Row
        return c

    @staticmethod
    def _to_dict(r):
        if r is None:
            return None
        d = dict(r)
        for k in ("input_data", "output_data"):
            if k in d and isinstance(d[k], str):
                try:
                    d[k] = json.loads(d[k])
                except (json.JSONDecodeError, TypeError):
                    logger.warning("Failed to parse agent execution JSON field '%s'", k, exc_info=True)
        return d

    def _exec(self, fn):
        conn = self._conn()
        try:
            return fn(conn)
        finally:
            conn.close()

    def submit_task(self, body, uid=None):
        def _do(conn):
            repo = AgentExecutionTasksRepository(conn)
            task_id = f"aet:{uuid.uuid4()}"
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            repo.create(
                {
                    "task_id": task_id,
                    "source": "internal",
                    "agent_role": body.agent_role,
                    "action_type": body.action_type,
                    "input_data": json.dumps(body.input_data, ensure_ascii=False),
                    "max_retries": body.max_retries,
                    "status": "completed",
                    "created_at": now,
                    "completed_at": now,
                    "duration_ms": 0,
                }
            )
            return self._to_dict(repo.get_by_task_id(task_id))

        return self._exec(_do)

    def list_tasks(self, status_filter=None, agent_role=None):
        def _do(conn):
            repo = AgentExecutionTasksRepository(conn)
            conds, pars = [], []
            if status_filter:
                conds.append("status=?")
                pars.append(status_filter)
            if agent_role:
                conds.append("agent_role=?")
                pars.append(agent_role)
            return [self._to_dict(r) for r in repo.list_all(conditions=conds or None, params=pars or None, order_by="created_at DESC")]

        return self._exec(_do)

    def get_task(self, task_id):
        def _do(conn):
            repo = AgentExecutionTasksRepository(conn)
            row = repo.get_by_task_id(task_id)
            if not row:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
            return self._to_dict(row)

        return self._exec(_do)

    def retry_task(self, task_id):
        def _do(conn):
            repo = AgentExecutionTasksRepository(conn)
            row = repo.get_by_task_id(task_id)
            if not row:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
            repo.update(row["id"], {"retry_count": row["retry_count"] + 1, "status": "pending"})
            return self._to_dict(repo.get_by_task_id(task_id))

        return self._exec(_do)

    def approve_task(self, task_id):
        def _do(conn):
            repo = AgentExecutionTasksRepository(conn)
            row = repo.get_by_task_id(task_id)
            if not row:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            repo.update(row["id"], {"status": "completed", "completed_at": now})
            return self._to_dict(repo.get_by_task_id(task_id))

        return self._exec(_do)

    def a2a_card(self):
        def _do(conn):
            rows = AgentSkillsRepository(conn).list_all(conditions=["enabled=1"], order_by="priority ASC")
            return {"name": "Cloud Agent", "skills": [s["skill_name"] for s in rows]}

        return self._exec(_do)

    def a2a_task(self, body):
        def _do(conn):
            repo = AgentExecutionTasksRepository(conn)
            task_id = body.task_id or f"aet:{uuid.uuid4()}"
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            repo.create(
                {
                    "task_id": task_id,
                    "source": "a2a",
                    "agent_role": body.agent_role,
                    "action_type": "process",
                    "input_data": json.dumps(body.input_data, ensure_ascii=False),
                    "status": "pending",
                    "created_at": now,
                }
            )
            return self._to_dict(repo.get_by_task_id(task_id))

        return self._exec(_do)
