"""Agent 运行时辅助方法，包含快照管理、回滚、日志持久化等。"""

import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class RuntimeHelper:
    """AgentRuntime 的混入类，提供快照管理、回滚、日志持久化等辅助方法。"""

    def _save_log(self, agent_key, goal, status, iterations, tool_calls, logs, started_at):
        try:
            self._agent_db.execute("ALTER TABLE agent_runtime_logs ADD COLUMN cost_data TEXT DEFAULT '{}'")
        except Exception:
            pass
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
                self._trace_id,
                json.dumps(self._cost_tracker),
            ),
        )
        self._agent_db.commit()

    def _save_snapshot(self, agent_key, step, plan, results, context, status="active"):
        try:
            self._snapshot_manager.save(agent_key, step, plan, results, context, status)
        except Exception:
            pass

    def _restore_from_snapshot(self, snapshot_id):
        data = self._snapshot_manager.load(snapshot_id)
        if data is None:
            return None
        return data

    def _try_rollback(self, agent_key):
        latest = self._snapshot_manager.get_latest(agent_key)
        if latest is None:
            return None
        self._snapshot_manager.mark_rolled_back(latest["id"])
        return (latest["plan"], latest["results"], latest["context"])

    def rollback_to(self, snapshot_id):
        data = self._restore_from_snapshot(snapshot_id)
        if data is None:
            return None
        self._snapshot_manager.mark_rolled_back(snapshot_id)
        return (data["plan"], data["results"], data["context"])

    def list_snapshots(self, agent_key, limit=10):
        return self._snapshot_manager.list_snapshots(agent_key, limit)

    def get_cost_usage(self) -> dict:
        return self._cost_governor.get_usage()
