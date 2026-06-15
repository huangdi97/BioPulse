"""Agent运行时核心模块，提供"规划-决策-反思-执行-验证"五阶段执行循环；通过RuntimeState状态管理与StateSnapshot快照回滚机制保障任务可靠执行。"""

import logging
import os
import threading
import time
import uuid
from datetime import datetime

from cloud.app.agent_runtime.bulkhead import Bulkhead
from cloud.app.agent_runtime.circuit_breaker import CircuitBreaker
from cloud.app.agent_runtime.content_filter import ContentBlocked, ContentFilter
from cloud.app.agent_runtime.cost_governor import CostGovernor
from cloud.app.agent_runtime.execution_loop import ExecutionLoopMixin
from cloud.app.agent_runtime.loop_detector import LoopDetector
from cloud.app.agent_runtime.memory import Memory
from cloud.app.agent_runtime.metrics import agent_active_count, agent_requests_total
from cloud.app.agent_runtime.models import RuntimeResult
from cloud.app.agent_runtime.notifier import Notifier
from cloud.app.agent_runtime.planner import Planner
from cloud.app.agent_runtime.rate_limiter import RateLimiter
from cloud.app.agent_runtime.reflector import Reflector
from cloud.app.agent_runtime.rollback_handler import RollbackHandlerMixin
from cloud.app.agent_runtime.runtime_core_tools import RuntimeCoreToolsMixin
from cloud.app.agent_runtime.runtime_helpers import RuntimeHelper
from cloud.app.agent_runtime.runtime_llm import RuntimeLLM
from cloud.app.agent_runtime.runtime_state import ApprovalManager, RuntimeState
from cloud.app.agent_runtime.runtime_tool_exec import RuntimeToolExecMixin
from cloud.app.agent_runtime.state_snapshot import StateSnapshot
from cloud.app.agent_runtime.streamer import AgentStreamer
from cloud.app.agent_runtime.tool_bridge import ToolBridge
from cloud.app.agent_runtime.tracer import AgentTracer
from cloud.app.agent_runtime.vector_memory import VectorMemory
from cloud.app.agent_runtime.verifier import Verifier

logger = logging.getLogger(__name__)

_agent_exec_semaphore: threading.Semaphore | None = None
_agent_sem_lock = threading.Lock()


def _get_global_semaphore() -> threading.Semaphore:
    global _agent_exec_semaphore
    if _agent_exec_semaphore is None:
        with _agent_sem_lock:
            if _agent_exec_semaphore is None:
                max_concurrency = int(os.getenv("AGENT_MAX_CONCURRENCY", "2"))
                _agent_exec_semaphore = threading.Semaphore(max_concurrency)
    return _agent_exec_semaphore


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
        self._rate_limiter = RateLimiter()
        self._circuit_breaker = CircuitBreaker()
        self._content_filter = ContentFilter()
        self._tracer = AgentTracer(self._agent_db)
        self._bulkhead = Bulkhead()
        self._vector_memory = VectorMemory()
        self._vector_memory.set_db(self._agent_db)
        self._streamer: AgentStreamer | None = None

    def set_streamer(self, streamer: AgentStreamer):
        """设置事件流推送器。"""
        self._streamer = streamer

    def execute(self, goal: str, agent_key: str, context: dict | None = None) -> RuntimeResult:
        """执行 Agent 任务，包含全局并发限流与舱壁隔离。"""
        sem = _get_global_semaphore()
        acquired = sem.acquire(blocking=True, timeout=120.0)
        if not acquired:
            return RuntimeResult(
                status="rate_limited",
                result="Global agent concurrency limit reached. Please try again later.",
                iterations=0,
                tool_calls=0,
                logs=[],
            )
        try:
            if not self._bulkhead.acquire(agent_key):
                return RuntimeResult(
                    status="bulkhead_rejected",
                    result=f"Agent '{agent_key}' is busy, too many concurrent executions. Try again later.",
                    iterations=0,
                    tool_calls=0,
                    logs=[],
                )
            try:
                return self._execute_with_bulkhead(goal, agent_key, context)
            finally:
                self._bulkhead.release(agent_key)
        finally:
            sem.release()

    def _execute_with_bulkhead(self, goal: str, agent_key: str, context: dict | None = None) -> RuntimeResult:
        trace_id = self._tracer.start_trace(agent_key, self._auth_header or "anonymous", {"goal": goal, "context": context})
        self._trace_id = trace_id
        agent_active_count.labels(agent_name=agent_key).inc()
        if self._streamer:
            self._streamer.stream(trace_id, "agent.start", {"agent_name": agent_key, "goal": goal, "context": context})
        try:
            injection_reason = self._content_filter.check_input(goal)
            if injection_reason:
                result = RuntimeResult(
                    status="blocked",
                    result=f"Input blocked by safety policy: {injection_reason}",
                    iterations=0,
                    tool_calls=0,
                    logs=[],
                )
                self._tracer.end_trace("blocked", result.model_dump())
                agent_requests_total.labels(agent_name=agent_key, status="blocked").inc()
                agent_active_count.labels(agent_name=agent_key).dec()
                return result
            user_key = f"user_agent:{self._auth_header or 'anonymous'}"
            self._rate_limiter.check_or_raise(user_key)
            memories = self._vector_memory.search(agent_key, goal, top_k=3)
            if memories:
                context = dict(context or {})
                context["_vector_memories"] = [{"key": m["key"], "content": m["content"], "score": m["score"]} for m in memories]
            result = self._execute_impl(goal, agent_key, context)
            if result.status == "success" and result.result:
                try:
                    self._content_filter.filter_output(result.result)
                except ContentBlocked:
                    result = RuntimeResult(
                        status="blocked",
                        result="Output blocked by safety policy",
                        iterations=result.iterations,
                        tool_calls=result.tool_calls,
                        logs=result.logs,
                        metadata=result.metadata,
                    )
                    self._tracer.end_trace("blocked", result.model_dump())
                    return result
            self._tracer.end_trace(result.status, result.model_dump())
            agent_requests_total.labels(agent_name=agent_key, status=result.status).inc()
            agent_active_count.labels(agent_name=agent_key).dec()
            if self._streamer:
                self._streamer.stream(trace_id, "agent.end", {"status": result.status, "result": result.result})
            return result
        except Exception:
            logger.exception("Runtime core异常")
            self._save_snapshot(agent_key, -1, [], [], context or {}, "failed")
            self._tracer.end_trace("error", {"error": "unhandled exception"})
            if self._streamer:
                self._streamer.stream(trace_id, "agent.error", {"error": "unhandled exception"})
            raise

    def resume(self, agent_key: str, goal: str, auth_header: str) -> RuntimeResult:
        """从检查点恢复 Agent 任务执行。"""
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
        """获取运行时状态统计。"""
        cur = self._agent_db.execute("SELECT status, COUNT(*) as cnt FROM agent_runtime_logs GROUP BY status")
        return {**self._stats, "by_status": {r["status"]: r["cnt"] for r in cur.fetchall()}}

    @property
    def brain(self) -> Memory:
        """获取 Agent 脑状态存储器。"""
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
