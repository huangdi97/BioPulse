import os
import sqlite3
from typing import Any, Generator

from cloud.app.services.platform_svc.tenant_isolation_service import CURRENT_TENANT

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
        conn.execute(
            "CREATE TABLE IF NOT EXISTS agent_traces ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "trace_id TEXT NOT NULL UNIQUE, "
            "agent_name TEXT NOT NULL, "
            "user_id TEXT DEFAULT '', "
            "input_data TEXT DEFAULT '{}', "
            "output_data TEXT DEFAULT '{}', "
            "status TEXT DEFAULT 'running', "
            "total_duration_ms INTEGER DEFAULT 0, "
            "total_prompt_tokens INTEGER DEFAULT 0, "
            "total_completion_tokens INTEGER DEFAULT 0, "
            "total_cost REAL DEFAULT 0.0, "
            "tool_calls_json TEXT DEFAULT '[]', "
            "llm_calls_json TEXT DEFAULT '[]', "
            "started_at TEXT DEFAULT (datetime('now')), "
            "ended_at TEXT"
            ")"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_traces_trace_id ON agent_traces(trace_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_traces_agent ON agent_traces(agent_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_traces_user ON agent_traces(user_id)")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS agent_cost_tracking ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "tenant_id TEXT DEFAULT 'default', "
            "agent_name TEXT NOT NULL, "
            "model TEXT NOT NULL, "
            "model_tier TEXT DEFAULT 'cloud_normal', "
            "task_type TEXT DEFAULT '', "
            "input_tokens INTEGER DEFAULT 0, "
            "output_tokens INTEGER DEFAULT 0, "
            "cost REAL DEFAULT 0.0, "
            "trace_id TEXT DEFAULT '', "
            "timestamp TEXT DEFAULT (datetime('now'))"
            ")"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cost_tracking_agent ON agent_cost_tracking(agent_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cost_tracking_model ON agent_cost_tracking(model)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cost_tracking_ts ON agent_cost_tracking(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cost_tracking_tenant ON agent_cost_tracking(tenant_id)")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS prompt_versions ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "agent_name TEXT NOT NULL, "
            "version_id INTEGER NOT NULL, "
            "content TEXT NOT NULL, "
            "created_at TEXT DEFAULT (datetime('now')), "
            "created_by TEXT DEFAULT 'system', "
            "UNIQUE(agent_name, version_id)"
            ")"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_prompt_versions_agent ON prompt_versions(agent_name)")
        conn.commit()


class TenantAwareConnection:
    def __init__(self, conn: sqlite3.Connection, tenant_id: str) -> None:
        self._conn = conn
        self._tenant_id = tenant_id

    @property
    def row_factory(self) -> Any:
        return self._conn.row_factory

    @row_factory.setter
    def row_factory(self, factory: Any) -> None:
        self._conn.row_factory = factory

    def execute(self, sql: str, parameters: Any = None) -> sqlite3.Cursor:
        sql, parameters = self._rewrite(sql, parameters or ())
        return self._conn.execute(sql, parameters)

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def _rewrite(self, sql: str, parameters: Any) -> tuple[str, Any]:
        tenant_id = self._tenant_id
        stripped = sql.strip()
        upper = stripped.upper()

        if upper.startswith("INSERT"):
            if "tenant_id" not in upper:
                col_end = upper.find("VALUES")
                cols = stripped[:col_end].rstrip()
                vals = stripped[col_end:]
                if cols.endswith(")"):
                    cols = cols[:-1] + ", tenant_id)"
                if vals.startswith("VALUES ("):
                    vals = "VALUES (?, " + vals[8:]
                elif vals.startswith("VALUES("):
                    vals = "VALUES(?," + vals[7:]
                sql = cols + " " + vals
                parameters = list(parameters) + [tenant_id]
        elif upper.startswith("SELECT") or upper.startswith("UPDATE") or upper.startswith("DELETE"):
            if "WHERE" in upper:
                for kw in ["GROUP BY", "ORDER BY", "LIMIT", "HAVING"]:
                    idx = upper.find(kw)
                    if idx != -1:
                        sql = sql[:idx] + "AND tenant_id=? " + sql[idx:]
                        break
                else:
                    sql += " AND tenant_id=?"
            else:
                for kw in ["GROUP BY", "ORDER BY", "LIMIT", "HAVING"]:
                    idx = upper.find(kw)
                    if idx != -1:
                        sql = sql[:idx] + "WHERE tenant_id=? " + sql[idx:]
                        break
                else:
                    sql += " WHERE tenant_id=?"
            parameters = list(parameters) + [tenant_id]

        return sql, parameters

    def __getattr__(self, name: str) -> Any:
        return getattr(self._conn, name)


def get_agent_db() -> Generator[sqlite3.Connection, None, None]:
    os.makedirs(os.path.dirname(AGENT_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(AGENT_DB_PATH)
    tenant_id = CURRENT_TENANT.get() or "default"
    wrapper = TenantAwareConnection(conn, tenant_id)
    wrapper.row_factory = sqlite3.Row
    try:
        yield wrapper
    finally:
        conn.close()


from cloud.app.agent_runtime_log_repository import (  # noqa: E402, F401
    AgentApprovalRepository,
    AgentRuntimeLogRepository,
)
