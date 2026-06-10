import os
import sqlite3
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
            "agent_name TEXT NOT NULL, "
            "model TEXT NOT NULL, "
            "model_tier TEXT DEFAULT 'cloud_normal', "
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


def get_agent_db() -> Generator[sqlite3.Connection, None, None]:
    os.makedirs(os.path.dirname(AGENT_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(AGENT_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


from cloud.app.agent_runtime_log_repository import (  # noqa: E402, F401
    AgentApprovalRepository,
    AgentRuntimeLogRepository,
)
