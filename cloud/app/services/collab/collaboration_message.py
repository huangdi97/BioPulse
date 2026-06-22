"""协作会话消息方法，包含步骤推进与完成逻辑。"""

import json

from fastapi import HTTPException

from cloud.app.repositories import CollaborationSessionsRepository, CollaborationStepsRepository


class CollaborationMessageMixin:
    """协作会话消息方法，提供步骤推进与完成管理。"""

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
        sess_repo = CollaborationSessionsRepository(self._connection())
        steps_repo = CollaborationStepsRepository(self._connection())

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
        steps_repo = CollaborationStepsRepository(self._connection())
        sess_repo = CollaborationSessionsRepository(self._connection())

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
