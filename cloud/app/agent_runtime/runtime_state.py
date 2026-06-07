"""运行时状态管理模块，包含检查点与审批管理器。"""

import json


class RuntimeState:
    """检查点管理器，持久化 Agent 运行状态以支持断点续跑。"""

    def __init__(self, agent_db):
        self._agent_db = agent_db

    def save(self, agent_key, goal, data, trace_id):
        json_data = json.dumps(data, ensure_ascii=False)
        cur = self._agent_db.execute(
            "UPDATE agent_runtime_logs SET checkpoint_data=?, trace_id=? WHERE agent_key=? AND goal=? AND status IN ('running', 'pending')",
            (json_data, trace_id, agent_key, goal),
        )
        if cur.rowcount == 0:
            self._agent_db.execute(
                "INSERT INTO agent_runtime_logs (agent_key, goal, status, checkpoint_data, trace_id) VALUES (?, ?, 'running', ?, ?)",
                (agent_key, goal, json_data, trace_id),
            )
        self._agent_db.commit()

    def load(self, agent_key, goal):
        cur = self._agent_db.execute(
            "SELECT checkpoint_data FROM agent_runtime_logs "
            "WHERE agent_key=? AND goal=? AND status='running' AND checkpoint_data IS NOT NULL "
            "ORDER BY id DESC LIMIT 1",
            (agent_key, goal),
        )
        row = cur.fetchone()
        if row and row["checkpoint_data"]:
            return json.loads(row["checkpoint_data"])
        return None

    def delete(self, agent_key, goal):
        self._agent_db.execute(
            "UPDATE agent_runtime_logs SET checkpoint_data=NULL WHERE agent_key=? AND goal=?",
            (agent_key, goal),
        )
        self._agent_db.commit()


class ApprovalManager:
    """审批管理器，创建待审批记录供人工审核后再恢复执行。"""

    def __init__(self, agent_db):
        self._agent_db = agent_db

    def create(self, trace_id, agent_key, goal, step, tool, params, reasoning):
        cur = self._agent_db.execute(
            "INSERT INTO agent_runtime_approvals (trace_id, agent_key, goal, step, tool, params, reasoning, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')",
            (trace_id, agent_key, goal, step, tool, json.dumps(params, ensure_ascii=False), reasoning),
        )
        self._agent_db.commit()
        return cur.lastrowid


CheckpointManager = RuntimeState
