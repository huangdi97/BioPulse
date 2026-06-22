"""编排服务，负责编排模板管理与多步骤协作流程的执行。"""

import json
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    AgentExecutionTasksRepository,
    CollaborationSessionsRepository,
    CollaborationStepsRepository,
    OrchestrationTemplatesRepository,
)
from shared.base_service import BaseService

logger = logging.getLogger(__name__)


def _row(r):
    if not r:
        return None
    d = dict(r)
    for k in ("steps",):
        if k in d and isinstance(d[k], str):
            try:
                d[k] = json.loads(d[k])
            except (json.JSONDecodeError, TypeError):
                logger.warning("Failed to parse orchestration template JSON field '%s'", k, exc_info=True)
    return d


def _rows(rows):
    return [_row(r) for r in rows]


class OrchestrateService(BaseService):
    """编排服务，提供编排模板管理与多步骤协作流程执行。"""

    def create_template(self, template_name: str, description: str, steps: list[dict], user_id: int) -> dict:
        """创建一个新的编排模板。"""
        tmpl_repo = OrchestrationTemplatesRepository(self._connection())
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row_id = tmpl_repo.create(
            {
                "template_name": template_name,
                "description": description,
                "steps": json.dumps(steps, ensure_ascii=False),
                "created_by": user_id,
                "created_at": now,
                "updated_at": now,
            }
        )
        row = tmpl_repo.get_by_id(row_id)
        return _row(row)

    def list_templates(self, enabled: Optional[int] = None) -> list:
        """查询编排模板列表，可选按启用状态过滤。"""
        tmpl_repo = OrchestrationTemplatesRepository(self._connection())
        conditions = []
        params = []
        if enabled is not None:
            conditions.append("enabled=?")
            params.append(enabled)
        rows = tmpl_repo.list_all(
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )
        return _rows(rows)

    def run_orchestration(self, template_name: str, context: dict) -> dict:
        """根据模板名称执行多步骤协同编排流程。"""
        tmpl_repo = OrchestrationTemplatesRepository(self._connection())
        placeholders = ", ".join(tmpl_repo.cols)
        tmpl = self.db.execute(
            f"SELECT {placeholders} FROM {tmpl_repo.table_name} WHERE template_name=? AND enabled=1",
            (template_name,),
        ).fetchone()
        if not tmpl:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Template not found or disabled")

        steps = json.loads(tmpl["steps"]) if isinstance(tmpl["steps"], str) else tmpl["steps"]
        if not steps:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Template has no steps")

        session_id = f"orch:{uuid.uuid4()}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sess_repo = CollaborationSessionsRepository(self._connection())
        sess_repo.create(
            {
                "session_id": session_id,
                "task_description": template_name,
                "source_agent_role": steps[0].get("agent_role", ""),
                "orchestrator_agent": "orchestrator",
                "routing_strategy": "pipeline",
                "involved_agents": json.dumps([s.get("agent_role", "") for s in steps], ensure_ascii=False),
                "total_steps": len(steps),
                "started_at": now,
            }
        )

        step_repo = CollaborationStepsRepository(self._connection())
        for i, step in enumerate(steps):
            order = i + 1
            agent_role = step.get("agent_role", "")
            action = step.get("action", "process")
            step_status = "running" if order == 1 else "pending"
            step_repo.create(
                {
                    "session_id": session_id,
                    "step_order": order,
                    "agent_role": agent_role,
                    "action_type": action,
                    "input_summary": json.dumps(context, ensure_ascii=False),
                    "status": step_status,
                    "started_at": now if order == 1 else None,
                }
            )

        task_repo = AgentExecutionTasksRepository(self._connection())
        for step in steps:
            agent_role = step.get("agent_role", "")
            action = step.get("action", "process")
            aet_task_id = f"aet:{uuid.uuid4()}"
            task_repo.create(
                {
                    "task_id": aet_task_id,
                    "source": "orchestrate",
                    "session_id": session_id,
                    "agent_role": agent_role,
                    "action_type": action,
                    "input_data": json.dumps(context, ensure_ascii=False),
                    "status": "pending",
                    "created_at": now,
                }
            )

        return {"session_id": session_id, "steps": len(steps)}
