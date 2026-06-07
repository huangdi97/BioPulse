"""Agent运行时核心模块，提供"规划-决策-反思-执行-验证"五阶段执行循环；通过RuntimeState状态管理与StateSnapshot快照回滚机制保障任务可靠执行。"""

import concurrent.futures
import json
import logging
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
from cloud.app.agent_runtime.runtime_helpers import RuntimeHelper
from cloud.app.agent_runtime.runtime_llm import RuntimeLLM
from cloud.app.agent_runtime.runtime_state import ApprovalManager, RuntimeState
from cloud.app.agent_runtime.state_snapshot import StateSnapshot
from cloud.app.agent_runtime.tool_bridge import ToolBridge
from cloud.app.agent_runtime.verifier import Verifier

logger = logging.getLogger(__name__)
_KEEP_CONTEXT = object()


class RuntimeCore(ExecutionLoopMixin, RollbackHandlerMixin, RuntimeHelper, RuntimeLLM):
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

    def _build_step_log(self, step, action, tool=None, params=None, result=None, duration_ms=0, **kw):
        entry = {
            "step": step,
            "action": action,
            "tool": tool,
            "params": params,
            "result": result,
            "duration_ms": duration_ms,
            "trace_id": self._trace_id,
        }
        entry.update(kw)
        return entry

    def _llm_meta(self, ai_resp=None, params=None, tool_output=None, include_tool_input=True):
        return {
            "llm_prompt": ai_resp.get("prompt") if ai_resp else None,
            "llm_raw_response": ai_resp.get("raw_response") if ai_resp else None,
            "llm_token_usage": ai_resp.get("usage") if ai_resp else None,
            "tool_input": json.dumps(params, ensure_ascii=False) if include_tool_input and params else None,
            "tool_output": tool_output,
            "retry_count": ai_resp.get("retry_count", 0) if ai_resp else 0,
        }

    def _check_budget(self, messages=None) -> bool:
        has_budget = messages is None or self._cost_governor.check("deepseek-chat", self._estimate_token_count(messages), 2048)
        return has_budget and not self._cost_governor.is_over_budget()

    def _accumulate_cost(self, ai_resp: dict, step: int) -> None:
        usage = ai_resp.get("usage", {})
        for target, source in (("prompt_tokens", "prompt_tokens"), ("completion_tokens", "completion_tokens"), ("total_tokens", "total_tokens")):
            self._cost_tracker[target] += usage.get(source, 0)
        cost = ai_resp.get("cost") or {
            "model_tier": ai_resp.get("model_tier", "cloud_normal"),
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        }
        self._cost_governor.record_step_cost(cost, step)
        summary = self.get_cost_usage()
        self._cost_tracker["total_cost"] = summary["total_cost"]
        self._cost_tracker["step_costs"] = summary["step_costs"]

    def _save_step_checkpoint(self, c, step, status="active", context=_KEEP_CONTEXT):
        context = c["context"] if context is _KEEP_CONTEXT else context
        self._save_checkpoint(
            c["agent_key"],
            c["goal"],
            self._make_checkpoint_state(
                c["agent_key"],
                c["goal"],
                step,
                c["messages"],
                c["logs"],
                c["tool_calls"],
                context,
                status,
            ),
        )

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

    def _handle_step_error(self, c, step, error_msg, tool=None, params=None, duration_ms=0, ai_resp=None):
        c["logs"].append(
            self._build_step_log(
                step,
                "error",
                tool=tool,
                params=params,
                result=error_msg,
                duration_ms=duration_ms,
                **self._llm_meta(ai_resp, params),
            )
        )
        self._save_step_checkpoint(c, step, "failed")
        rolled = self._try_rollback(c["agent_key"])
        if not rolled:
            return False
        c["messages"], c["logs"], c["context"] = rolled
        return True

    def _is_completed(self, decision) -> bool:
        return decision.action == "complete"

    def _handle_completion(self, c, step, decision, ai_resp, duration_ms):
        c["logs"].append(
            self._build_step_log(
                step,
                "complete",
                result=decision.reasoning or "",
                duration_ms=duration_ms,
                **self._llm_meta(ai_resp, include_tool_input=False),
            )
        )
        self._save_step_checkpoint(c, step, "completed")
        return self._finish(c, "completed", decision.reasoning or "任务完成", step, step + 1, True, notify=True, delete_checkpoint=True)

    def _handle_loop_detected(self, c, step, tool_name, tool_params, loop_result, duration_ms):
        c["logs"].append(self._build_step_log(step, "loop_detected", tool=tool_name, params=tool_params, result=loop_result, duration_ms=duration_ms))
        self._save_step_checkpoint(c, step, "escalated")
        return self._finish(c, "escalated", f"检测到循环: {loop_result}", step, step + 1, False)

    def _handle_approval_needed(self, c, step, tool_name, tool_params, decision):
        self._save_step_checkpoint(c, step, "awaiting_approval", context=None)
        approval_id = self._approval.create(self._trace_id, c["agent_key"], c["goal"], step, tool_name, tool_params, decision.reasoning or "")
        return self._finish(
            c,
            "awaiting_approval",
            f"需要人工审批: {tool_name}",
            step,
            step,
            None,
            metadata={"approval_id": approval_id},
            notify=True,
        )

    def _handle_max_iterations(self, c, max_iter):
        return self._finish(c, "max_iterations", "达到最大迭代次数", max_iter - 1, max_iter, False, notify=True)

    def _append_invalid_step(self, c, step, message, duration_ms, ai_resp, tool=None, params=None):
        c["logs"].append(
            self._build_step_log(
                step,
                "error",
                tool=tool,
                params=params,
                result=message,
                duration_ms=duration_ms,
                **self._llm_meta(ai_resp, include_tool_input=False),
            )
        )
        self._save_step_checkpoint(c, step, "invalid")

    def _reflect_before_tool(self, step, goal, agent_key, context, messages, decision, ai_resp, llm_duration_ms, logs):
        level = self._select_reflector_level(context, llm_duration_ms)
        started, result, reflected_params, status = time.time(), None, decision.params or {}, "pass"
        try:
            review_context = {
                "agent_key": agent_key,
                "runtime_context": context or {},
                "messages": messages if level == "thorough" else messages[-3:],
                "cost": self.get_cost_usage(),
                "llm_usage": ai_resp.get("usage"),
                "trace_id": self._trace_id,
            }
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            future = executor.submit(self._reflector.review_decision, goal, decision, review_context, level)
            try:
                result = future.result(timeout=self._reflector_timeout_seconds)
            except concurrent.futures.TimeoutError:
                future.cancel()
                status = "timeout_pass"
            finally:
                executor.shutdown(wait=False, cancel_futures=True)
        except Exception as exc:
            status = "error_pass"
            logger.info("Reflector soft-pass after error at level=%s: %s", level, exc)
        if result is not None:
            status = result.action or "pass"
            if result.action == "adjust_params" and result.plan and result.plan.steps:
                reflected_params = result.plan.steps[-1].params_template
        self._update_reflector_level(level, status in {"pass", "timeout_pass", "error_pass"})
        detail = result.detail if result is not None else status
        logger.info("Reflector level=%s result=%s detail=%s", level, status, detail)
        logs.append(
            self._build_step_log(
                step,
                "reflector",
                tool=decision.tool,
                params=decision.params or {},
                result={
                    "level": level,
                    "status": status,
                    "detail": detail,
                    "next_level": self._reflector_level,
                },
                duration_ms=int((time.time() - started) * 1000),
                **self._llm_meta(ai_resp, decision.params or {}, include_tool_input=True),
            )
        )
        return reflected_params

    def _select_reflector_level(self, context: dict | None, llm_duration_ms: int) -> str:
        requested = (context or {}).get("reflector_level")
        if requested in {"thorough", "balanced", "light"}:
            self._reflector_level = requested
            return requested
        if llm_duration_ms > 5000:
            self._reflector_level = "light"
        return self._reflector_level

    def _update_reflector_level(self, level: str, no_issue: bool) -> None:
        if level != "light" or not no_issue:
            self._reflector_light_clean_streak = 0
            return
        self._reflector_light_clean_streak += 1
        if self._reflector_light_clean_streak >= 3:
            self._reflector_level = "balanced"
            self._reflector_light_clean_streak = 0


AgentRuntime = RuntimeCore
