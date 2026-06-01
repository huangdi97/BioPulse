import json
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
from cloud.app.services.base import BaseService


def _row(r):
    if not r:
        return None
    d = dict(r)
    for k in ("steps",):
        if k in d and isinstance(d[k], str):
            try:
                d[k] = json.loads(d[k])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


def _rows(rows):
    return [_row(r) for r in rows]


class OrchestrateService(BaseService):
    def create_template(
        self, template_name: str, description: str, steps: list[dict], user_id: int
    ) -> dict:
        tmpl_repo = OrchestrationTemplatesRepository(self.db)
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
        tmpl_repo = OrchestrationTemplatesRepository(self.db)
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
        tmpl_repo = OrchestrationTemplatesRepository(self.db)
        placeholders = ", ".join(tmpl_repo.cols)
        tmpl = self.db.execute(
            f"SELECT {placeholders} FROM {tmpl_repo.table_name} WHERE template_name=? AND enabled=1",
            (template_name,),
        ).fetchone()
        if not tmpl:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail="Template not found or disabled"
            )

        steps = (
            json.loads(tmpl["steps"])
            if isinstance(tmpl["steps"], str)
            else tmpl["steps"]
        )
        if not steps:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail="Template has no steps"
            )

        session_id = f"orch:{uuid.uuid4()}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sess_repo = CollaborationSessionsRepository(self.db)
        sess_repo.create(
            {
                "session_id": session_id,
                "task_description": template_name,
                "source_agent_role": steps[0].get("agent_role", ""),
                "orchestrator_agent": "orchestrator",
                "routing_strategy": "pipeline",
                "involved_agents": json.dumps(
                    [s.get("agent_role", "") for s in steps], ensure_ascii=False
                ),
                "total_steps": len(steps),
                "started_at": now,
            }
        )

        step_repo = CollaborationStepsRepository(self.db)
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

        task_repo = AgentExecutionTasksRepository(self.db)
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
