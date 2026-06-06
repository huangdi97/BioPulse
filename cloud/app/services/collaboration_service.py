"""协作服务，管理 Agent 技能注册、协作会话与语义路由。"""

import json
import uuid
from typing import Optional

from fastapi import HTTPException

from cloud.app.repositories import (
    AgentSkillsRepository,
    CollaborationSessionsRepository,
    CollaborationStepsRepository,
)
from cloud.app.services.base import BaseService


class CollaborationService(BaseService):
    """协作服务，提供技能管理、会话编排与语义路由功能。"""

    def register_skill(
        self,
        skill_name: str,
        agent_role: str,
        description: str,
        entity_types: list[str],
        capabilities: list[str],
        confidence: float,
        priority: int,
    ) -> dict:
        repo = AgentSkillsRepository(self.db)
        row_id = repo.create(
            {
                "skill_name": skill_name,
                "agent_role": agent_role,
                "description": description,
                "entity_types": json.dumps(entity_types, ensure_ascii=False),
                "capabilities": json.dumps(capabilities, ensure_ascii=False),
                "confidence": confidence,
                "priority": priority,
            }
        )
        return repo.get_by_id(row_id)

    def list_skills(self, agent_role: Optional[str] = None, enabled: Optional[int] = None) -> list:
        repo = AgentSkillsRepository(self.db)
        conditions, params = [], []
        if agent_role:
            conditions.append("agent_role=?")
            params.append(agent_role)
        if enabled is not None:
            conditions.append("enabled=?")
            params.append(enabled)
        return repo.list_all(
            conditions=conditions or None,
            params=params or None,
            order_by="priority ASC",
        )

    def delete_skill(self, skill_id: int) -> None:
        repo = AgentSkillsRepository(self.db)
        row = repo.get_by_id(skill_id)
        if not row:
            raise HTTPException(status_code=404, detail="Skill not found")
        repo.delete(skill_id)

    def create_session(
        self,
        task_description: str,
        source_entity_id: str,
        source_agent_role: str,
        orchestrator_agent: str,
        routing_strategy: str,
    ) -> dict:
        repo = CollaborationSessionsRepository(self.db)
        sid = f"collab:{uuid.uuid4()}"
        repo.create(
            {
                "session_id": sid,
                "task_description": task_description,
                "source_entity_id": source_entity_id,
                "source_agent_role": source_agent_role,
                "orchestrator_agent": orchestrator_agent,
                "routing_strategy": routing_strategy,
            }
        )
        rows = repo.list_all(conditions=["session_id=?"], params=[sid])
        return rows[0] if rows else None

    def add_session_step(
        self,
        session_id: str,
        agent_role: str,
        action_type: str,
        input_summary: str,
        entity_id: str,
    ) -> dict:
        sess_repo = CollaborationSessionsRepository(self.db)
        steps_repo = CollaborationStepsRepository(self.db)

        sess_rows = sess_repo.list_all(conditions=["session_id=?"], params=[session_id])
        if not sess_rows:
            raise HTTPException(status_code=404, detail="Session not found")
        sess = sess_rows[0]

        all_steps = steps_repo.list_all(conditions=["session_id=?"], params=[session_id], order_by="step_order ASC")
        current_order = max((s["step_order"] for s in all_steps), default=0)
        step_order = current_order + 1
        is_first = step_order == 1
        step_status = "running" if is_first else "pending"

        step_id = steps_repo.create(
            {
                "session_id": session_id,
                "step_order": step_order,
                "agent_role": agent_role,
                "action_type": action_type,
                "input_summary": input_summary,
                "entity_id": entity_id,
                "status": step_status,
            }
        )

        agents = json.loads(sess.get("involved_agents") or "[]")
        if agent_role not in agents:
            agents.append(agent_role)
        sess_repo.update(
            sess["id"],
            {
                "involved_agents": json.dumps(agents, ensure_ascii=False),
                "total_steps": step_order,
            },
        )

        return steps_repo.get_by_id(step_id)

    def complete_step(
        self,
        session_id: str,
        step_id: int,
        output_summary: str,
        status_val: str,
        duration_seconds: int,
    ) -> dict:
        steps_repo = CollaborationStepsRepository(self.db)
        sess_repo = CollaborationSessionsRepository(self.db)

        step = steps_repo.list_all(conditions=["id=?", "session_id=?"], params=[step_id, session_id])
        if not step:
            raise HTTPException(status_code=404, detail="Step not found")

        steps_repo.update(
            step_id,
            {
                "output_summary": output_summary,
                "status": status_val,
                "duration_seconds": duration_seconds,
            },
        )

        completed = steps_repo.count(conditions=["session_id=?", "status='completed'"], params=[session_id])
        total = steps_repo.count(conditions=["session_id=?"], params=[session_id])

        all_done = completed >= total
        sess_rows = sess_repo.list_all(conditions=["session_id=?"], params=[session_id])
        if sess_rows:
            sess_repo.update(
                sess_rows[0]["id"],
                {
                    "completed_steps": completed,
                    "status": "completed" if all_done else "active",
                },
            )

        row = steps_repo.get_by_id(step_id)
        sess_row = sess_repo.list_all(conditions=["session_id=?"], params=[session_id])
        return {"step": row, "session": sess_row[0] if sess_row else None}

    def list_sessions(
        self,
        status: Optional[str] = None,
        source_agent_role: Optional[str] = None,
        routing_strategy: Optional[str] = None,
    ) -> list:
        repo = CollaborationSessionsRepository(self.db)
        conditions, params = [], []
        if status:
            conditions.append("status=?")
            params.append(status)
        if source_agent_role:
            conditions.append("source_agent_role=?")
            params.append(source_agent_role)
        if routing_strategy:
            conditions.append("routing_strategy=?")
            params.append(routing_strategy)
        return repo.list_all(
            conditions=conditions or None,
            params=params or None,
            order_by="started_at DESC",
        )

    def get_session(self, session_id: str) -> dict:
        sess_repo = CollaborationSessionsRepository(self.db)
        steps_repo = CollaborationStepsRepository(self.db)
        sess_rows = sess_repo.list_all(conditions=["session_id=?"], params=[session_id])
        if not sess_rows:
            raise HTTPException(status_code=404, detail="Session not found")
        steps = steps_repo.list_all(conditions=["session_id=?"], params=[session_id], order_by="step_order ASC")
        return {"session": sess_rows[0], "steps": steps}

    def semantic_route(
        self,
        task_description: str,
        entity_type: str,
        entity_id: str,
        routing_strategy: str,
    ) -> dict:
        repo = AgentSkillsRepository(self.db)
        if entity_type:
            like = f"%{entity_type}%"
            skills = repo.list_all(
                conditions=["enabled=1", "entity_types LIKE ?"],
                params=[like],
                order_by="priority ASC, confidence DESC",
            )
        else:
            skills = repo.list_all(conditions=["enabled=1"], order_by="priority ASC, confidence DESC")

        if not skills:
            raise HTTPException(status_code=404, detail="No matching agent skills found")

        return {
            "task_description": task_description,
            "entity_type": entity_type,
            "routing_strategy": routing_strategy,
            "matched_skills": skills,
            "best_match": skills[0],
        }

    def dashboard(self) -> dict:
        skills_repo = AgentSkillsRepository(self.db)
        sess_repo = CollaborationSessionsRepository(self.db)
        steps_repo = CollaborationStepsRepository(self.db)

        total_skills = skills_repo.count()
        active_skills = skills_repo.count(conditions=["enabled=1"])
        total_sessions = sess_repo.count()
        active_sessions = sess_repo.count(conditions=["status='active'"])
        completed_sessions = sess_repo.count(conditions=["status='completed'"])
        total_steps = steps_repo.count()
        completed_steps = steps_repo.count(conditions=["status='completed'"])

        top_skills = steps_repo.list_all(order_by="agent_role ASC")
        role_counts = {}
        for s in top_skills:
            role = s["agent_role"]
            role_counts[role] = role_counts.get(role, 0) + 1
        top_agent_roles = sorted(
            [{"agent_role": k, "step_count": v} for k, v in role_counts.items()],
            key=lambda x: x["step_count"],
            reverse=True,
        )[:5]

        recent = sess_repo.list_all(order_by="started_at DESC")[:5]

        return {
            "skills": {"total": total_skills, "active": active_skills},
            "sessions": {
                "total": total_sessions,
                "active": active_sessions,
                "completed": completed_sessions,
            },
            "steps": {"total": total_steps, "completed": completed_steps},
            "top_agent_roles": top_agent_roles,
            "recent_sessions": recent,
        }
