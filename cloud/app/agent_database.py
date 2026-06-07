import os
import sqlite3
from datetime import datetime
from typing import Generator

AGENT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "cloud_agent.db",
)


def init_agent_db() -> None:
    os.makedirs(os.path.dirname(AGENT_DB_PATH), exist_ok=True)
    with sqlite3.connect(AGENT_DB_PATH) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS agent_runtime_logs ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "agent_key TEXT NOT NULL, "
            "goal TEXT NOT NULL, "
            "status TEXT DEFAULT 'pending', "
            "iterations INTEGER DEFAULT 0, "
            "tool_calls INTEGER DEFAULT 0, "
            "result TEXT, "
            "error_message TEXT, "
            "started_at TEXT, "
            "completed_at TEXT, "
            "log_detail TEXT DEFAULT '[]', "
            "created_at TEXT DEFAULT (datetime('now')), "
            "checkpoint_data TEXT DEFAULT NULL, "
            "trace_id TEXT DEFAULT '', "
            "cost_data TEXT DEFAULT '{}'"
            ")"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_runtime_logs_agent ON agent_runtime_logs(agent_key)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_runtime_logs_status ON agent_runtime_logs(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_runtime_logs_trace ON agent_runtime_logs(trace_id)")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS agent_runtime_approvals ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "trace_id TEXT NOT NULL, "
            "agent_key TEXT NOT NULL, "
            "goal TEXT NOT NULL, "
            "step INTEGER DEFAULT 0, "
            "tool TEXT NOT NULL, "
            "params TEXT DEFAULT '{}', "
            "reasoning TEXT DEFAULT '', "
            "status TEXT DEFAULT 'pending', "
            "created_at TEXT DEFAULT (datetime('now')), "
            "responded_at TEXT, "
            "responded_by TEXT DEFAULT ''"
            ")"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_approvals_status ON agent_runtime_approvals(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_approvals_trace ON agent_runtime_approvals(trace_id)")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS agent_brains ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "agent_key TEXT NOT NULL, "
            "user_id INTEGER DEFAULT 0, "
            "key TEXT NOT NULL, "
            "value TEXT NOT NULL, "
            "value_type TEXT DEFAULT 'str', "
            "updated_at TEXT DEFAULT (datetime('now')), "
            "UNIQUE(agent_key, user_id, key)"
            ")"
        )
        conn.execute(
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
        conn.execute("CREATE INDEX IF NOT EXISTS idx_state_snapshots_agent ON agent_state_snapshots(agent_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_state_snapshots_status ON agent_state_snapshots(status)")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS agent_runtime_snapshots ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "trace_id TEXT NOT NULL, "
            "step INTEGER NOT NULL, "
            "state_json TEXT NOT NULL, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
            "expires_at TIMESTAMP"
            ")"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_runtime_snapshots_trace_step ON agent_runtime_snapshots(trace_id, step)")
        conn.commit()


def get_agent_db() -> Generator[sqlite3.Connection, None, None]:
    os.makedirs(os.path.dirname(AGENT_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(AGENT_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


class AgentRuntimeLogRepository:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def get_logs(self, agent_key: str | None = None, status: str | None = None, page: int = 1, page_size: int = 20) -> dict:
        conditions = []
        params = []
        if agent_key:
            conditions.append("agent_key = ?")
            params.append(agent_key)
        if status:
            conditions.append("status = ?")
            params.append(status)
        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        offset = (page - 1) * page_size
        total = self.db.execute(f"SELECT COUNT(*) as cnt FROM agent_runtime_logs{where}", params).fetchone()["cnt"]
        rows = self.db.execute(
            f"SELECT * FROM agent_runtime_logs{where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [page_size, offset],
        ).fetchall()
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [dict(r) for r in rows],
        }

    def create_log(
        self,
        agent_key: str,
        goal: str,
        status: str = "pending",
        iterations: int = 0,
        tool_calls: int = 0,
        log_detail: str = "[]",
        started_at: str | None = None,
        completed_at: str | None = None,
        trace_id: str = "",
        cost_data: str = "{}",
        result: str | None = None,
        error_message: str | None = None,
        checkpoint_data: str | None = None,
    ) -> int:
        cur = self.db.execute(
            "INSERT INTO agent_runtime_logs "
            "(agent_key, goal, status, iterations, tool_calls, log_detail, "
            "started_at, completed_at, trace_id, cost_data, result, error_message, checkpoint_data) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                agent_key,
                goal,
                status,
                iterations,
                tool_calls,
                log_detail,
                started_at,
                completed_at,
                trace_id,
                cost_data,
                result,
                error_message,
                checkpoint_data,
            ),
        )
        self.db.commit()
        return cur.lastrowid

    def update_status(
        self, log_id: int, status: str, result: str | None = None, error_message: str | None = None, completed_at: str | None = None
    ) -> bool:
        sets = ["status = ?"]
        params: list = [status]
        if result is not None:
            sets.append("result = ?")
            params.append(result)
        if error_message is not None:
            sets.append("error_message = ?")
            params.append(error_message)
        if completed_at is not None:
            sets.append("completed_at = ?")
            params.append(completed_at)
        params.append(log_id)
        cur = self.db.execute(f"UPDATE agent_runtime_logs SET {', '.join(sets)} WHERE id = ?", params)
        self.db.commit()
        return cur.rowcount > 0


class AgentApprovalRepository:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def get_approvals(self, status: str = "pending") -> list[dict]:
        rows = self.db.execute(
            "SELECT * FROM agent_runtime_approvals WHERE status = ? ORDER BY created_at ASC",
            (status,),
        ).fetchall()
        return [dict(r) for r in rows]

    def approve(self, approval_id: int, responded_by: str = "") -> bool:
        now = datetime.now().isoformat()
        cur = self.db.execute(
            "UPDATE agent_runtime_approvals SET status = 'approved', responded_at = ?, responded_by = ? WHERE id = ? AND status = 'pending'",
            (now, responded_by, approval_id),
        )
        self.db.commit()
        return cur.rowcount > 0

    def reject(self, approval_id: int, responded_by: str = "") -> bool:
        now = datetime.now().isoformat()
        cur = self.db.execute(
            "UPDATE agent_runtime_approvals SET status = 'rejected', responded_at = ?, responded_by = ? WHERE id = ? AND status = 'pending'",
            (now, responded_by, approval_id),
        )
        self.db.commit()
        return cur.rowcount > 0
