"""状态快照模块，保存/加载 Agent 运行过程的全量状态。"""

import json
from datetime import datetime


class SnapshotManager:
    """Agent 状态快照管理器，支持保存、加载、回滚及自动清理。"""

    def __init__(self, agent_db):
        self._agent_db = agent_db
        self._create_table()

    def _create_table(self):
        self._agent_db.execute(
            "CREATE TABLE IF NOT EXISTS agent_state_snapshots ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "agent_id TEXT NOT NULL, "
            "step_id INTEGER DEFAULT 0, "
            "plan_json TEXT DEFAULT '[]', "
            "results_json TEXT DEFAULT '[]', "
            "context_json TEXT DEFAULT '{}', "
            "created_at TEXT DEFAULT CURRENT_TIMESTAMP, "
            "status TEXT DEFAULT 'active'"
            ")"
        )
        self._agent_db.execute("CREATE INDEX IF NOT EXISTS idx_state_snapshots_agent ON agent_state_snapshots(agent_id)")
        self._agent_db.execute("CREATE INDEX IF NOT EXISTS idx_state_snapshots_status ON agent_state_snapshots(status)")
        self._agent_db.commit()

    def _serialize(self, obj):
        return json.dumps(obj, ensure_ascii=False, default=str)

    def _deserialize(self, text, default):
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return default

    def save(self, agent_id, step_id, plan, results, context, status="active"):
        plan_json = self._serialize(plan)
        results_json = self._serialize(results)
        context_json = self._serialize(context)
        created_at = datetime.now().isoformat()

        cur = self._agent_db.execute(
            "INSERT INTO agent_state_snapshots "
            "(agent_id, step_id, plan_json, results_json, context_json, created_at, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (agent_id, step_id, plan_json, results_json, context_json, created_at, status),
        )
        self._agent_db.commit()

        snapshot_id = cur.lastrowid
        self._cleanup(agent_id)
        return snapshot_id

    def load(self, snapshot_id):
        row = self._agent_db.execute(
            "SELECT * FROM agent_state_snapshots WHERE id=?",
            (snapshot_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "agent_id": row["agent_id"],
            "step_id": row["step_id"],
            "plan": self._deserialize(row["plan_json"], []),
            "results": self._deserialize(row["results_json"], []),
            "context": self._deserialize(row["context_json"], {}),
            "created_at": row["created_at"],
            "status": row["status"],
        }

    def list_snapshots(self, agent_id, limit=10):
        rows = self._agent_db.execute(
            "SELECT id, agent_id, step_id, created_at, status FROM agent_state_snapshots WHERE agent_id=? ORDER BY id DESC LIMIT ?",
            (agent_id, limit),
        ).fetchall()
        return [
            {
                "id": r["id"],
                "agent_id": r["agent_id"],
                "step_id": r["step_id"],
                "created_at": r["created_at"],
                "status": r["status"],
            }
            for r in rows
        ]

    def get_latest(self, agent_id):
        row = self._agent_db.execute(
            "SELECT * FROM agent_state_snapshots WHERE agent_id=? AND status='active' ORDER BY id DESC LIMIT 1",
            (agent_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "agent_id": row["agent_id"],
            "step_id": row["step_id"],
            "plan": self._deserialize(row["plan_json"], []),
            "results": self._deserialize(row["results_json"], []),
            "context": self._deserialize(row["context_json"], {}),
            "created_at": row["created_at"],
            "status": row["status"],
        }

    def mark_rolled_back(self, snapshot_id):
        self._agent_db.execute(
            "UPDATE agent_state_snapshots SET status='rolled_back' WHERE id=?",
            (snapshot_id,),
        )
        self._agent_db.commit()

    def _cleanup(self, agent_id):
        self._agent_db.execute(
            "DELETE FROM agent_state_snapshots WHERE agent_id=? AND id NOT IN ("
            "SELECT id FROM agent_state_snapshots WHERE agent_id=? "
            "ORDER BY id DESC LIMIT 50"
            ")",
            (agent_id, agent_id),
        )
        self._agent_db.commit()
