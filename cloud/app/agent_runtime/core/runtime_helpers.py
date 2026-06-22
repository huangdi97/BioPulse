"""Agent 运行时辅助方法，包含快照管理、回滚、日志持久化等。"""

import json
import logging
import sqlite3
from datetime import datetime

from cloud.app.agent_runtime.memory.state_snapshot import load_snapshot, save_snapshot
from cloud.app.agent_runtime.memory.state_snapshot import recover as recover_fn

logger = logging.getLogger(__name__)


class CompositionHelper:
    """通过组合提供的纯工具类，封装快照管理、回滚、日志持久化等辅助方法。"""

    def __init__(self, agent_db, core):
        self._agent_db = agent_db
        self._core = core

    def _save_log(self, agent_key, goal, status, iterations, tool_calls, logs, started_at):
        try:
            self._agent_db.execute("ALTER TABLE agent_runtime_logs ADD COLUMN cost_data TEXT DEFAULT '{}'")
        except sqlite3.OperationalError:
            logger.warning("agent_runtime_logs.cost_data already exists, skipping migration")
        self._agent_db.execute(
            "INSERT INTO agent_runtime_logs (agent_key, goal, status, iterations, tool_calls, log_detail, "
            "started_at, completed_at, trace_id, cost_data) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                agent_key,
                goal,
                status,
                iterations,
                tool_calls,
                json.dumps(logs, ensure_ascii=False),
                started_at,
                datetime.now().isoformat(),
                self._core._trace_id,
                json.dumps(self._core.get_cost_usage(), ensure_ascii=False),
            ),
        )
        self._agent_db.commit()

    def _make_checkpoint_state(self, agent_key, goal, step, messages, logs, tool_calls_so_far, context, status="active"):
        return {
            "trace_id": self._core._trace_id,
            "step": step,
            "messages": messages,
            "logs": logs,
            "tool_calls_so_far": tool_calls_so_far,
            "goal": goal,
            "agent_key": agent_key,
            "context": context,
            "trace": self._core._trace_data,
            "cost": self._core.get_cost_usage(),
            "status": status,
        }

    def _save_checkpoint(self, agent_key, goal, state):
        save_snapshot(self._agent_db, self._core._trace_id, state["step"], state)
        self._core._checkpoint.save(agent_key, goal, state, self._core._trace_id)

    def _load_checkpoint(self, agent_key, goal):
        row = self._agent_db.execute(
            "SELECT trace_id FROM agent_runtime_logs "
            "WHERE agent_key=? AND goal=? AND status='running' AND checkpoint_data IS NOT NULL AND trace_id != '' "
            "ORDER BY id DESC LIMIT 1",
            (agent_key, goal),
        ).fetchone()
        if row and row["trace_id"]:
            latest = self._core._snapshot_manager.load_runtime_latest(row["trace_id"])
            if latest:
                return latest["state"]
        checkpoint = self._core._checkpoint.load(agent_key, goal)
        if checkpoint and checkpoint.get("trace_id"):
            latest = self._core._snapshot_manager.load_runtime_latest(checkpoint["trace_id"])
            if latest:
                return latest["state"]
        return checkpoint

    def _save_snapshot(self, agent_key, step, plan, results, context, status="active"):
        try:
            self._core._snapshot_manager.save(agent_key, step, plan, results, context, status)
        except (KeyError, TypeError, ValueError):
            logger.exception("Failed to save snapshot for agent %s at step %s", agent_key, step)

    def _restore_from_snapshot(self, snapshot_id):
        data = self._core._snapshot_manager.load(snapshot_id)
        if data is None:
            return None
        return data

    def _try_rollback(self, agent_key):
        latest_runtime = self._core._snapshot_manager.load_runtime_latest(self._core._trace_id)
        if latest_runtime:
            state = latest_runtime["state"]
            return (state.get("messages", []), state.get("logs", []), state.get("context"))
        latest = self._core._snapshot_manager.get_latest(agent_key)
        if latest is None:
            return None
        self._core._snapshot_manager.mark_rolled_back(latest["id"])
        return (latest["plan"], latest["results"], latest["context"])

    def rollback_to(self, snapshot_id):
        """回滚到指定快照。"""
        data = self._restore_from_snapshot(snapshot_id)
        if data is None:
            return None
        self._core._snapshot_manager.mark_rolled_back(snapshot_id)
        return (data["plan"], data["results"], data["context"])

    def _load_runtime_snapshot(self, trace_id, step):
        snapshot = load_snapshot(self._agent_db, trace_id, step)
        if snapshot:
            return snapshot["state"]
        return None

    def list_snapshots(self, agent_key, limit=10):
        """列出指定 agent 的快照列表。"""
        return self._core._snapshot_manager.list_snapshots(agent_key, limit)

    def get_cost_usage(self) -> dict:
        """获取当前成本使用详情。"""
        return self._core._cost_governor.get_usage()

    def get_status(self) -> dict:
        """获取运行时状态统计。"""
        cur = self._agent_db.execute("SELECT status, COUNT(*) as cnt FROM agent_runtime_logs GROUP BY status")
        return {**self._core._stats, "by_status": {r["status"]: r["cnt"] for r in cur.fetchall()}}

    def list_recoverable(self) -> list[dict]:
        """列出所有可恢复的checkpoint（中断且未过期）。"""
        snapshots = recover_fn(self._agent_db)
        result = []
        for snap in snapshots:
            state = snap.get("state", {})
            result.append(
                {
                    "trace_id": snap.get("trace_id", ""),
                    "agent_key": state.get("agent_key", ""),
                    "goal": state.get("goal", ""),
                    "step": snap.get("step", 0),
                    "created_at": snap.get("created_at", ""),
                    "status": state.get("status", "interrupted"),
                }
            )
        return result

    def scan_recoverable_checkpoints(self) -> None:
        """启动时扫描可恢复的checkpoint并记录日志。"""
        recoverable = self.list_recoverable()
        if recoverable:
            logger.info("Found %d recoverable checkpoints on startup", len(recoverable))
            for ck in recoverable:
                logger.info(
                    "Recoverable checkpoint: trace=%s agent=%s goal=%s step=%s",
                    ck["trace_id"],
                    ck["agent_key"],
                    ck["goal"][:50],
                    ck["step"],
                )
        else:
            logger.info("No recoverable checkpoints found on startup")
