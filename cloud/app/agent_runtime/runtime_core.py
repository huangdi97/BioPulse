"""Agent运行时核心模块，提供"规划-决策-反思-执行-验证"五阶段执行循环；通过RuntimeState状态管理与StateSnapshot快照回滚机制保障任务可靠执行。"""

import time
import uuid
from datetime import datetime

from cloud.app.agent_runtime.cost_governor import CostGovernor
from cloud.app.agent_runtime.execution_loop import ExecutionLoopMixin
from cloud.app.agent_runtime.loop_detector import LoopDetector
from cloud.app.agent_runtime.memory import Memory
from cloud.app.agent_runtime.models import RuntimeResult
from cloud.app.agent_runtime.notifier import Notifier
from cloud.app.agent_runtime.planner import Planner
from cloud.app.agent_runtime.reflector import Reflector
from cloud.app.agent_runtime.rollback_handler import RollbackHandlerMixin
from cloud.app.agent_runtime.runtime_core_tools import RuntimeCoreToolsMixin
from cloud.app.agent_runtime.runtime_helpers import RuntimeHelper
from cloud.app.agent_runtime.runtime_llm import RuntimeLLM
from cloud.app.agent_runtime.runtime_state import ApprovalManager, RuntimeState
from cloud.app.agent_runtime.runtime_tool_exec import RuntimeToolExecMixin
from cloud.app.agent_runtime.state_snapshot import StateSnapshot
from cloud.app.agent_runtime.tool_bridge import ToolBridge
from cloud.app.agent_runtime.verifier import Verifier


class RuntimeCore(ExecutionLoopMixin, RollbackHandlerMixin, RuntimeHelper, RuntimeLLM, RuntimeCoreToolsMixin, RuntimeToolExecMixin):
    def __init__(self, agent_db, business_db, auth_header: str, notifier: Notifier | None = None):
        self._agent_db, self._db, self._auth_header, self._notifier = agent_db, business_db, auth_header, notifier
        self._tool_registry = ToolBridge()
        self._tool_registry.register_default_tools()
        self._brain = Memory(agent_db)
        self._tool_registry.set_brain(self._brain)
        self._stats = {"total_runs": 0, "success_count": 0, "fail_count": 0}
        self._trace_id = str(uuid.uuid4())
        self._cost_tracker = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "total_cost": 0.0, "step_costs": []}
        self._loop_detector, self._checkpoint = LoopDetector(), RuntimeState(agent_db)
        self._approval, self._snapshot_manager, self._cost_governor = ApprovalManager(agent_db), StateSnapshot(agent_db), CostGovernor()
        self._planner = Planner()
        self._reflector = Reflector(plan_generator=self._planner)
        self._reflector_level, self._reflector_light_clean_streak, self._reflector_timeout_seconds = "balanced", 0, 2.0
        self._verifier = Verifier()
        self._trace_data: list[dict] = []

    def execute(self, goal: str, agent_key: str, context: dict | None = None) -> RuntimeResult:
        try:
            return self._execute_impl(goal, agent_key, context)
        except Exception:
            self._save_snapshot(agent_key, -1, [], [], context or {}, "failed")
            raise

    def resume(self, agent_key: str, goal: str, auth_header: str) -> RuntimeResult:
        checkpoint = self._load_checkpoint(agent_key, goal)
        if not checkpoint:
            return RuntimeResult(status="error", result="no checkpoint found", iterations=0, tool_calls=0, logs=[])
        approval = self._agent_db.execute(
            "SELECT * FROM agent_runtime_approvals WHERE trace_id=? AND status='approved' ORDER BY id DESC LIMIT 1",
            (checkpoint["trace_id"],),
        ).fetchone()
        if not approval:
            return RuntimeResult(status="awaiting_approval", result="still pending approval", iterations=0, tool_calls=0, logs=[])
        self._trace_id = checkpoint["trace_id"]
        self._auth_header = auth_header
        return self.execute(goal, agent_key, checkpoint.get("context"))

    def get_status(self) -> dict:
        cur = self._agent_db.execute("SELECT status, COUNT(*) as cnt FROM agent_runtime_logs GROUP BY status")
        return {**self._stats, "by_status": {r["status"]: r["cnt"] for r in cur.fetchall()}}

    @property
    def brain(self) -> Memory:
        return self._brain

    def _notify(self, c, status):
        if self._notifier:
            elapsed = (datetime.now() - datetime.fromisoformat(c["started_at"])).total_seconds()
            self._notifier.notify(c["agent_key"], c["goal"], status, elapsed, self._cost_tracker)

    def _finish(self, c, status, result, step, iterations, success=None, metadata=None, notify=False, delete_checkpoint=False):
        self._save_log(c["agent_key"], c["goal"], status, iterations, c["tool_calls"], c["logs"], c["started_at"])
        if notify:
            self._notify(c, status)
        if delete_checkpoint:
            self._checkpoint.delete(c["agent_key"], c["goal"])
        if success is not None:
            self._stats["total_runs"] += 1
            self._stats["success_count" if success else "fail_count"] += 1
        data = {"trace_id": self._trace_id, "cost": self.get_cost_usage()}
        data.update(metadata or {})
        return RuntimeResult(status=status, result=result, iterations=iterations, tool_calls=c["tool_calls"], logs=c["logs"], metadata=data)

    def _handle_budget_exceeded(self, c, step, step_start):
        c["logs"].append(
            self._build_step_log(
                step,
                "budget_exceeded",
                result="cost budget exceeded",
                duration_ms=int((time.time() - step_start) * 1000),
            )
        )
        self._save_step_checkpoint(c, step, "budget_exceeded")
        return self._finish(c, "budget_exceeded", "cost budget exceeded", step, step + 1, False)

    def _is_completed(self, decision) -> bool:
        return decision.action == "complete"


AgentRuntime = RuntimeCore
