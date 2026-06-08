"""协作会话管理方法。"""

import json
import uuid
from typing import Optional

from fastapi import HTTPException

from cloud.app.repositories import CollaborationSessionsRepository, CollaborationStepsRepository


class CollaborationSessionMixin:
    """协作会话创建、步骤推进和查询方法。"""

    def create_session(
        self,
        task_description: str,
        source_entity_id: str,
        source_agent_role: str,
        orchestrator_agent: str,
        routing_strategy: str,
    ) -> dict:
        """创建一个新的协作会话。

        Args:
            task_description: 任务描述
            source_entity_id: 发起协作的实体 ID
            source_agent_role: 发起 Agent 的角色
            orchestrator_agent: 编排 Agent 名称
            routing_strategy: 路由策略标识

        Returns:
            新创建的会话记录字典
        """
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
        """向协作会话中添加一个新的执行步骤。

        Args:
            session_id: 协作会话 ID
            agent_role: 执行该步骤的 Agent 角色
            action_type: 动作类型
            input_summary: 输入摘要
            entity_id: 关联的实体 ID

        Returns:
            新创建的步骤记录字典

        Raises:
            HTTPException: 会话不存在时返回 404
        """
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
        """标记协作步骤为完成状态并更新会话进度。

        Args:
            session_id: 协作会话 ID
            step_id: 步骤 ID
            output_summary: 输出摘要
            status_val: 步骤状态值 (如 "completed", "failed")
            duration_seconds: 执行耗时（秒）

        Returns:
            包含更新后的步骤和会话信息的字典

        Raises:
            HTTPException: 步骤不存在时返回 404
        """
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
        """按条件查询协作会话列表。

        Args:
            status: 可选，按会话状态过滤
            source_agent_role: 可选，按发起 Agent 角色过滤
            routing_strategy: 可选，按路由策略过滤

        Returns:
            会话记录列表，按开始时间降序排列
        """
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
        """获取指定会话及其所有步骤的详细信息。

        Args:
            session_id: 协作会话 ID

        Returns:
            包含 session 和 steps 键的字典

        Raises:
            HTTPException: 会话不存在时返回 404
        """
        sess_repo = CollaborationSessionsRepository(self.db)
        steps_repo = CollaborationStepsRepository(self.db)
        sess_rows = sess_repo.list_all(conditions=["session_id=?"], params=[session_id])
        if not sess_rows:
            raise HTTPException(status_code=404, detail="Session not found")
        steps = steps_repo.list_all(conditions=["session_id=?"], params=[session_id], order_by="step_order ASC")
        return {"session": sess_rows[0], "steps": steps}
