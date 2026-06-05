import os
import sqlite3
from typing import Generator

from cloud.app.schema import SCHEMA_SQL
from cloud.app.seeds import (
    seed_agent_data,
    seed_brain_memory,  # seed_identity, seed_privacy,  # ❄️ 冻结
    seed_collaboration,
    seed_compliance_v2,
    seed_decision_intel,
    seed_event_bus,
    seed_hcp_sandbox,
    seed_kg,
    seed_market_intel,
    seed_mdt_engine,
    seed_memory_gates,
    seed_memory_s1,
    seed_memory_utility,
    seed_recommend,
    seed_route_rules,
    seed_s2,
    seed_s3,
    seed_s4,
    seed_s5,
    seed_s6,
    seed_soap_decision,
    seed_training_coach,
    seed_world_tree,
)
from cloud.app.seeds.seed_model_compression import seed_model_compression
from cloud.seed_data import seed_products
from shared.db import PGCompatConnection

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "cloud.db",
)

DATABASE_URL = os.getenv("DATABASE_URL", "")


def get_db() -> Generator:
    if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"):
        import psycopg2

        conn = PGCompatConnection(psycopg2.connect(DATABASE_URL))
        try:
            yield conn
        finally:
            conn.close()
    else:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()


def _ensure_token_budget_tables(conn) -> None:
    """Create token_budget and token_usage tables if they don't exist (migration)."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS token_budget ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "user_id INTEGER NOT NULL, "
        "model TEXT NOT NULL, "
        "daily_used INTEGER NOT NULL DEFAULT 0, "
        "alert_sent INTEGER NOT NULL DEFAULT 0, "
        "updated_at TEXT DEFAULT CURRENT_TIMESTAMP"
        ")"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_token_budget_user ON token_budget(user_id, model)")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS token_usage ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "user_id INTEGER NOT NULL, "
        "model TEXT NOT NULL, "
        "tokens INTEGER NOT NULL DEFAULT 0, "
        "cost REAL NOT NULL DEFAULT 0.0, "
        "usage_date TEXT NOT NULL, "
        "created_at TEXT DEFAULT CURRENT_TIMESTAMP"
        ")"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_token_usage_user ON token_usage(user_id, model, usage_date)")
    conn.commit()


def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA_SQL)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS federated_nodes ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "node_id TEXT UNIQUE NOT NULL, "
            "node_name TEXT DEFAULT '', "
            "node_type TEXT DEFAULT 'partner', "
            "organization TEXT DEFAULT '', "
            "status TEXT DEFAULT 'pending', "
            "endpoint_url TEXT DEFAULT '', "
            "public_key TEXT DEFAULT '', "
            "data_summary TEXT DEFAULT '{}', "
            "last_heartbeat TEXT DEFAULT '', "
            "round_count INTEGER DEFAULT 0, "
            "total_samples INTEGER DEFAULT 0, "
            "reliability_score REAL DEFAULT 0.0, "
            "is_active INTEGER DEFAULT 1, "
            "registered_at TEXT DEFAULT CURRENT_TIMESTAMP, "
            "updated_at TEXT DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS audit_chain_blocks ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "block_hash TEXT UNIQUE NOT NULL, "
            "prev_block_hash TEXT DEFAULT '', "
            "block_data TEXT DEFAULT '{}', "
            "block_type TEXT DEFAULT 'audit', "
            "created_by TEXT DEFAULT '', "
            "node_id TEXT DEFAULT '', "
            "timestamp TEXT DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        _ensure_token_budget_tables(conn)
        seed_market_intel(conn)
        seed_agent_data(conn)
        seed_decision_intel(conn)
        seed_compliance_v2(conn)
        seed_mdt_engine(conn)
        seed_memory_gates(conn)
        seed_world_tree(conn)
        seed_route_rules(conn)
        seed_hcp_sandbox(conn)
        seed_training_coach(conn)
        seed_soap_decision(conn)
        seed_memory_utility(conn)
        seed_brain_memory(conn)
        # seed_identity(conn)  # ❄️ 冻结
        # seed_privacy(conn)  # ❄️ 冻结
        seed_kg(conn)
        seed_recommend(conn)
        seed_collaboration(conn)
        seed_event_bus(conn)
        seed_memory_s1(conn)
        seed_s2(conn)
        seed_s3(conn)
        seed_s4(conn)
        seed_s5(conn)
        seed_s6(conn)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS model_compression_jobs ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "job_id TEXT NOT NULL UNIQUE, "
            "model_name TEXT NOT NULL, "
            "compression_type TEXT NOT NULL, "
            "original_size_bytes INTEGER NOT NULL DEFAULT 0, "
            "compressed_size_bytes INTEGER NOT NULL DEFAULT 0, "
            "compression_ratio REAL NOT NULL DEFAULT 0.0, "
            "accuracy_impact REAL NOT NULL DEFAULT 0.0, "
            "parameters_before INTEGER NOT NULL DEFAULT 0, "
            "parameters_after INTEGER NOT NULL DEFAULT 0, "
            "status TEXT NOT NULL DEFAULT 'pending', "
            "result_detail TEXT DEFAULT '', "
            "started_at TEXT, "
            "completed_at TEXT, "
            "created_at TEXT DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        seed_model_compression(conn)
        seed_products(conn)
        for col in [
            "source_sub TEXT DEFAULT ''",
        ]:
            try:
                conn.execute(f"ALTER TABLE effect_metrics ADD COLUMN {col}")
            except Exception:
                pass
        try:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_em_source_sub ON effect_metrics(source_sub)")
        except Exception:
            pass
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            ("photo_watermark", "off"),
        )
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            ("location_mode", "auto"),
        )
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            ("storage_provider", "local"),
        )
        conn.executescript(
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
            "created_at TEXT DEFAULT (datetime('now'))"
            ");"
            "CREATE INDEX IF NOT EXISTS idx_runtime_logs_agent ON agent_runtime_logs(agent_key);"
            "CREATE INDEX IF NOT EXISTS idx_runtime_logs_status ON agent_runtime_logs(status);"
        )
        for col in [
            "checkpoint_data TEXT DEFAULT NULL",
            "trace_id TEXT DEFAULT ''",
        ]:
            try:
                conn.execute(f"ALTER TABLE agent_runtime_logs ADD COLUMN {col}")
            except Exception:
                pass
        conn.execute("CREATE INDEX IF NOT EXISTS idx_runtime_logs_trace ON agent_runtime_logs(trace_id)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_runtime_approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT NOT NULL,
                agent_key TEXT NOT NULL,
                goal TEXT NOT NULL,
                step INTEGER DEFAULT 0,
                tool TEXT NOT NULL,
                params TEXT DEFAULT '{}',
                reasoning TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now')),
                responded_at TEXT,
                responded_by TEXT DEFAULT ''
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_approvals_status ON agent_runtime_approvals(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_approvals_trace ON agent_runtime_approvals(trace_id)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_brains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_key TEXT NOT NULL,
                user_id INTEGER DEFAULT 0,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                value_type TEXT DEFAULT 'str',
                updated_at TEXT DEFAULT (datetime('now')),
                UNIQUE(agent_key, user_id, key)
            )
        """)
        conn.commit()
