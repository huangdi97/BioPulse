"""Durable Execution — 每步后自动 checkpoint 状态到 SQLite，支持断点恢复与 pending 列表查询。"""

import json
import logging
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DB_PATH = Path("data/durable_execution.db")


class DurableExecutor:
    """checkpoint + restore + list_pending — LangGraph 级 durable execution。"""

    def __init__(self, db_path: str | Path = _DB_PATH):
        self._db_path = Path(db_path)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS checkpoints (
                    agent_key TEXT NOT NULL,
                    trace_id TEXT NOT NULL,
                    step INTEGER NOT NULL,
                    state_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at REAL NOT NULL,
                    PRIMARY KEY (agent_key, trace_id, step)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_checkpoints_pending
                ON checkpoints(agent_key, trace_id, status)
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def checkpoint(self, agent_key: str, trace_id: str, state_dict: dict[str, Any], step: int = 0) -> None:
        """保存当前状态到 SQLite。"""
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO checkpoints
                    (agent_key, trace_id, step, state_json, status, created_at)
                    VALUES (?, ?, ?, ?, 'active', ?)
                    """,
                    (agent_key, trace_id, step, json.dumps(state_dict), time.time()),
                )
            logger.debug("Checkpoint saved: agent=%s trace=%s step=%d", agent_key, trace_id, step)

    def restore(self, agent_key: str, trace_id: str) -> dict[str, Any] | None:
        """从最近 checkpoint 恢复状态。"""
        with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    """
                    SELECT state_json FROM checkpoints
                    WHERE agent_key=? AND trace_id=? AND status='active'
                    ORDER BY step DESC LIMIT 1
                    """,
                    (agent_key, trace_id),
                ).fetchone()
        if row is None:
            logger.warning("No checkpoint found for agent=%s trace=%s", agent_key, trace_id)
            return None
        return json.loads(row["state_json"])

    def list_pending(self) -> list[dict[str, Any]]:
        """列出所有未完成的 Agent 执行（用于重启后恢复）。"""
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT agent_key, trace_id, MAX(step) as step, MAX(created_at) as last_active
                    FROM checkpoints
                    WHERE status='active'
                    GROUP BY agent_key, trace_id
                    ORDER BY last_active DESC
                    """
                ).fetchall()
        return [dict(r) for r in rows]

    def mark_completed(self, agent_key: str, trace_id: str) -> None:
        """标记执行完成，不再恢复。"""
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE checkpoints SET status='completed' WHERE agent_key=? AND trace_id=?",
                    (agent_key, trace_id),
                )
            logger.info("Marked completed: agent=%s trace=%s", agent_key, trace_id)

    def mark_failed(self, agent_key: str, trace_id: str) -> None:
        """标记执行失败。"""
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE checkpoints SET status='failed' WHERE agent_key=? AND trace_id=?",
                    (agent_key, trace_id),
                )
