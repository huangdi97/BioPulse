"""数据库初始化与种子数据。"""

import logging
import os
import sqlite3
from typing import Generator

from cloud.app.schemas.ddl import SCHEMA_SQL
from cloud.app.seeds import (
    seed_agent_data,
    seed_brain_memory,
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
from cloud.seed_products import seed_products
from shared.config import settings
from shared.db import PGCompatConnection

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "cloud.db",
)

DATABASE_URL = settings.database_url

_engine = None


def _get_engine():
    global _engine
    if _engine is None and (DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")):
        from sqlalchemy import create_engine

        pool_size = int(os.environ.get("DB_POOL_SIZE", "10"))
        max_overflow = int(os.environ.get("DB_MAX_OVERFLOW", "20"))
        _engine = create_engine(
            DATABASE_URL,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
        )
    return _engine


def get_db() -> Generator:
    if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"):
        import psycopg

        conn = PGCompatConnection(psycopg.connect(DATABASE_URL))
        try:
            yield conn
        finally:
            conn.close()
    else:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
        finally:
            conn.close()


def _ensure_effect_metrics_source_sub(conn) -> None:
    """Backfill source_sub before SCHEMA_SQL creates its index on older databases."""
    exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='effect_metrics'").fetchone()
    if not exists:
        return
    columns = {row[1] for row in conn.execute("PRAGMA table_info(effect_metrics)").fetchall()}
    if "source_sub" not in columns:
        conn.execute("ALTER TABLE effect_metrics ADD COLUMN source_sub TEXT DEFAULT ''")
        conn.commit()


def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        _ensure_effect_metrics_source_sub(conn)
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
        _ensure_effect_metrics_source_sub(conn)
        try:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_em_source_sub ON effect_metrics(source_sub)")
        except Exception:
            logger.warning("CREATE INDEX idx_em_source_sub 失败")
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
        conn.commit()
