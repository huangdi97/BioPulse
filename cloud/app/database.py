import os
import sqlite3
from typing import Generator

from shared.db import PGCompatConnection

from cloud.app.schema import SCHEMA_SQL
from cloud.app.seeds import (
    seed_market_intel, seed_agent_data, seed_decision_intel,
    seed_compliance_v2, seed_mdt_engine, seed_memory_gates,
    seed_world_tree, seed_route_rules, seed_hcp_sandbox,
    seed_training_coach, seed_soap_decision, seed_memory_utility,
    seed_brain_memory,  # seed_identity, seed_privacy,  # ❄️ 冻结
    seed_kg,
    seed_recommend, seed_collaboration, seed_event_bus,
    seed_memory_s1, seed_s2, seed_s3, seed_s4, seed_s5, seed_s6,
)
from cloud.seed_data import seed_products

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
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_token_budget_user ON token_budget(user_id, model)"
    )
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
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_token_usage_user ON token_usage(user_id, model, usage_date)"
    )
    conn.commit()


def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA_SQL)
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
        seed_products(conn)
        conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("photo_watermark", "off"))
        conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("location_mode", "auto"))
        conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("storage_provider", "local"))
        conn.commit()
