"""Agent 运行时核心，编排 LLM 推理、工具调用、循环检测与状态持久化。"""

import concurrent.futures
import json
import logging
import time
import uuid
from datetime import datetime

from fastapi import HTTPException

from cloud.app.agent_runtime.agent_specs import AGENT_SPECS
from cloud.app.agent_runtime.cost_governor import CostGovernor
from cloud.app.agent_runtime.guard import sanitize_tool_output
from cloud.app.agent_runtime.loop_detector import LoopDetector
from cloud.app.agent_runtime.memory import AgentBrain
from cloud.app.agent_runtime.models import RuntimeResult
from cloud.app.agent_runtime.notifier import AgentNotifier
from cloud.app.agent_runtime.planner import PlanGenerator
from cloud.app.agent_runtime.reflector import Reflector
from cloud.app.agent_runtime.runtime_helpers import RuntimeHelper
from cloud.app.agent_runtime.runtime_llm import RuntimeLLM
from cloud.app.agent_runtime.runtime_state import ApprovalManager, CheckpointManager
from cloud.app.agent_runtime.state_snapshot import SnapshotManager
from cloud.app.agent_runtime.tool_bridge import ToolRegistry
from cloud.app.agent_runtime.validator import AgentOutputValidator
from cloud.app.agent_runtime.verifier import Verifier

logger = logging.getLogger(__name__)


class AgentRuntime(RuntimeHelper, RuntimeLLM):
    """Agent 运行时主控制器，管理 LLM 对话循环、工具调用、检查点与审批流程。"""

    def __init__(self, agent_db, business_db, auth_header: str, notifier: AgentNotifier | None = None):
        self._agent_db = agent_db
        self._db = business_db
        self._auth_header = auth_header
        self._notifier = notifier
        self._tool_registry = ToolRegistry()
        self._tool_registry.register_default_tools()
        self._brain = AgentBrain(agent_db)
        self._tool_registry.set_brain(self._brain)
        self._stats = {"total_runs": 0, "success_count": 0, "fail_count": 0}
        self._trace_id = str(uuid.uuid4())
        self._cost_tracker = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "total_cost": 0.0, "step_costs": []}
        self._loop_detector = LoopDetector()
        self._checkpoint = CheckpointManager(agent_db)
        self._approval = ApprovalManager(agent_db)
        self._snapshot_manager = SnapshotManager(agent_db)
        self._cost_governor = CostGovernor()
        self._planner = PlanGenerator()
        self._reflector = Reflector(plan_generator=self._planner)
        self._reflector_level = "balanced"
        self._reflector_light_clean_streak = 0
        self._reflector_timeout_seconds = 2.0
        self._verifier = Verifier()
        self._trace_data: list[dict] = []

    def _make_log(self, step, action, tool=None, params=None, result=None, duration_ms=0, **kw):
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

    def execute(self, goal: str, agent_key: str, context: dict | None = None) -> RuntimeResult:
        try:
            return self._execute_impl(goal, agent_key, context)
        except Exception:
            self._save_snapshot(agent_key, -1, [], [], context or {}, "failed")
            raise

    def _execute_impl(self, goal: str, agent_key: str, context: dict | None = None) -> RuntimeResult:
        spec = AGENT_SPECS.get(agent_key)
        if spec is None:
            return RuntimeResult(status="error", result=f"unknown agent_key: {agent_key}", iterations=0, tool_calls=0, logs=[])

        logs = []
        tool_calls = 0
        max_iter = min(spec["max_iterations"], 15)
        started_at = datetime.now().isoformat()

        checkpoint = self._load_checkpoint(agent_key, goal)
        if checkpoint:
            messages = checkpoint["messages"]
            logs = checkpoint["logs"]
            tool_calls = checkpoint["tool_calls_so_far"]
            start_step = checkpoint["step"] + 1
        else:
            system_prompt = (
                f"你是一个{spec['role_desc']}\n\n"
                f"可用工具（JSON格式）：{json.dumps(self._tool_registry.list_tools(), ensure_ascii=False)}\n\n"
                f"当前上下文：{json.dumps(context or {}, ensure_ascii=False)}\n\n"
                '请回复JSON格式：{"action": "call_tool"|"complete"|"error", "tool": "tool_name", "params": {...}, "reasoning": "..."}'
            )
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": goal},
            ]
            start_step = 0

        approved_tool = None
        approved_tool_params = None
        if checkpoint:
            app = self._agent_db.execute(
                "SELECT tool, params FROM agent_runtime_approvals WHERE agent_key=? AND goal=? AND status='approved' ORDER BY id DESC LIMIT 1",
                (agent_key, goal),
            ).fetchone()
            if app:
                approved_tool = app["tool"]
                approved_tool_params = json.loads(app["params"]) if app["params"] else {}

        plan = self._planner.plan(goal, agent_key, context)
        logs.append(plan)

        for step in range(start_step, max_iter):
            messages = self._compress_messages(messages)
            step_start = time.time()

            if approved_tool and step == start_step:
                tool_result = self._tool_registry.call(approved_tool, approved_tool_params, self._auth_header, caller_permission="write")
                self._verifier.verify(tool_result)
                if tool_result.get("needs_approval"):
                    tool_result = {"success": False, "data": None, "error": "still requires approval"}
                tool_calls += 1
                tool_output_text = json.dumps(tool_result, ensure_ascii=False)
                safe_output = sanitize_tool_output(tool_output_text)
                duration_ms = int((time.time() - step_start) * 1000)
                logs.append(
                    self._make_log(
                        step,
                        "call_tool",
                        tool=approved_tool,
                        params=approved_tool_params,
                        result=safe_output,
                        duration_ms=duration_ms,
                        llm_prompt=None,
                        llm_raw_response=None,
                        llm_token_usage=None,
                        tool_input=json.dumps(approved_tool_params, ensure_ascii=False),
                        tool_output=tool_output_text,
                        retry_count=0,
                    )
                )
                messages.append(
                    {
                        "role": "assistant",
                        "content": json.dumps({"action": "call_tool", "tool": approved_tool, "params": approved_tool_params}, ensure_ascii=False),
                    }
                )
                messages.append({"role": "user", "content": f"工具返回：{safe_output}"})
                approved_tool = None
                self._save_checkpoint(
                    agent_key,
                    goal,
                    self._make_checkpoint_state(agent_key, goal, step, messages, logs, tool_calls, context),
                )
                continue

            estimated_input = self._estimate_token_count(messages)
            estimated_output = 2048
            if not self._cost_governor.check("deepseek-chat", estimated_input, estimated_output):
                logs.append(
                    self._make_log(step, "budget_exceeded", result="cost budget exceeded", duration_ms=int((time.time() - step_start) * 1000))
                )
                self._save_checkpoint(
                    agent_key,
                    goal,
                    self._make_checkpoint_state(agent_key, goal, step, messages, logs, tool_calls, context, "budget_exceeded"),
                )
                self._save_log(agent_key, goal, "budget_exceeded", step + 1, tool_calls, logs, started_at)
                self._stats["total_runs"] += 1
                self._stats["fail_count"] += 1
                return RuntimeResult(
                    status="budget_exceeded",
                    result="cost budget exceeded",
                    iterations=step + 1,
                    tool_calls=tool_calls,
                    logs=logs,
                    metadata={"trace_id": self._trace_id, "cost": self.get_cost_usage()},
                )
            try:
                ai_resp = self._call_ai(messages, spec["default_temperature"], step, force_level=None)
                usage = ai_resp.get("usage", {})
                self._cost_tracker["prompt_tokens"] += usage.get("prompt_tokens", 0)
                self._cost_tracker["completion_tokens"] += usage.get("completion_tokens", 0)
                self._cost_tracker["total_tokens"] += usage.get("total_tokens", 0)
                cost_data = ai_resp.get("cost") or {
                    "model_tier": ai_resp.get("model_tier", "cloud_normal"),
                    "input_tokens": usage.get("prompt_tokens", 0),
                    "output_tokens": usage.get("completion_tokens", 0),
                }
                self._cost_governor.record_step_cost(cost_data, step)
                usage_summary = self.get_cost_usage()
                self._cost_tracker["total_cost"] = usage_summary["total_cost"]
                self._cost_tracker["step_costs"] = usage_summary["step_costs"]
            except Exception as e:
                logs.append(
                    self._make_log(
                        step,
                        "error",
                        result=str(e),
                        duration_ms=int((time.time() - step_start) * 1000),
                        llm_prompt=None,
                        llm_raw_response=None,
                        llm_token_usage=None,
                        tool_input=None,
                        tool_output=None,
                        retry_count=0,
                    )
                )
                self._save_checkpoint(
                    agent_key,
                    goal,
                    self._make_checkpoint_state(agent_key, goal, step, messages, logs, tool_calls, context, "failed"),
                )
                rolled_back = self._try_rollback(agent_key)
                if rolled_back:
                    messages, logs, context = rolled_back
                    continue
                raise

            if self._cost_governor.is_over_budget():
                logs.append(
                    self._make_log(step, "budget_exceeded", result="cost budget exceeded", duration_ms=int((time.time() - step_start) * 1000))
                )
                self._save_checkpoint(
                    agent_key,
                    goal,
                    self._make_checkpoint_state(agent_key, goal, step, messages, logs, tool_calls, context, "budget_exceeded"),
                )
                self._save_log(agent_key, goal, "budget_exceeded", step + 1, tool_calls, logs, started_at)
                self._stats["total_runs"] += 1
                self._stats["fail_count"] += 1
                return RuntimeResult(
                    status="budget_exceeded",
                    result="cost budget exceeded",
                    iterations=step + 1,
                    tool_calls=tool_calls,
                    logs=logs,
                    metadata={"trace_id": self._trace_id, "cost": self.get_cost_usage()},
                )

            duration_ms = int((time.time() - step_start) * 1000)
            reply = ai_resp["reply"]

            decision, validation_error = AgentOutputValidator.validate(reply)
            if validation_error or decision is None:
                logs.append(
                    self._make_log(
                        step,
                        "error",
                        result=validation_error or "invalid decision",
                        duration_ms=duration_ms,
                        llm_prompt=ai_resp.get("prompt"),
                        llm_raw_response=ai_resp.get("raw_response"),
                        llm_token_usage=ai_resp.get("usage"),
                        tool_input=None,
                        tool_output=None,
                        retry_count=ai_resp.get("retry_count", 0),
                    )
                )
                self._save_checkpoint(
                    agent_key,
                    goal,
                    self._make_checkpoint_state(agent_key, goal, step, messages, logs, tool_calls, context, "invalid"),
                )
                continue

            action = decision.action
            tool_name = decision.tool
            tool_params = decision.params or {}

            if action == "complete":
                logs.append(
                    self._make_log(
                        step,
                        "complete",
                        result=decision.reasoning or "",
                        duration_ms=duration_ms,
                        llm_prompt=ai_resp.get("prompt"),
                        llm_raw_response=ai_resp.get("raw_response"),
                        llm_token_usage=ai_resp.get("usage"),
                        tool_input=None,
                        tool_output=None,
                        retry_count=ai_resp.get("retry_count", 0),
                    )
                )
                self._save_checkpoint(
                    agent_key,
                    goal,
                    self._make_checkpoint_state(agent_key, goal, step, messages, logs, tool_calls, context, "completed"),
                )
                self._save_log(agent_key, goal, "completed", step + 1, tool_calls, logs, started_at)
                if self._notifier:
                    self._notifier.notify(
                        agent_key, goal, "completed", (datetime.now() - datetime.fromisoformat(started_at)).total_seconds(), self._cost_tracker
                    )
                self._checkpoint.delete(agent_key, goal)
                self._stats["total_runs"] += 1
                self._stats["success_count"] += 1
                return RuntimeResult(
                    status="completed",
                    result=decision.reasoning or "任务完成",
                    iterations=step + 1,
                    tool_calls=tool_calls,
                    logs=logs,
                    metadata={"trace_id": self._trace_id, "cost": self.get_cost_usage()},
                )

            if action == "call_tool" and tool_name:
                tool_params = self._reflect_before_tool(
                    step=step,
                    goal=goal,
                    agent_key=agent_key,
                    context=context,
                    messages=messages,
                    decision=decision,
                    ai_resp=ai_resp,
                    llm_duration_ms=duration_ms,
                    logs=logs,
                )
                try:
                    tool_result = self._tool_registry.call(
                        tool_name, tool_params, self._auth_header, caller_permission=spec.get("max_permission", "read")
                    )
                    self._verifier.verify(tool_result)
                except Exception as e:
                    logs.append(
                        self._make_log(
                            step,
                            "error",
                            tool=tool_name,
                            params=tool_params,
                            result=str(e),
                            duration_ms=duration_ms,
                            llm_prompt=ai_resp.get("prompt"),
                            llm_raw_response=ai_resp.get("raw_response"),
                            llm_token_usage=ai_resp.get("usage"),
                            tool_input=json.dumps(tool_params, ensure_ascii=False),
                            tool_output=None,
                            retry_count=ai_resp.get("retry_count", 0),
                        )
                    )
                    self._save_checkpoint(
                        agent_key,
                        goal,
                        self._make_checkpoint_state(agent_key, goal, step, messages, logs, tool_calls, context, "failed"),
                    )
                    rolled_back = self._try_rollback(agent_key)
                    if rolled_back:
                        messages, logs, context = rolled_back
                        continue
                    raise

                if tool_result.get("needs_approval"):
                    self._save_checkpoint(
                        agent_key,
                        goal,
                        self._make_checkpoint_state(agent_key, goal, step, messages, logs, tool_calls, None, "awaiting_approval"),
                    )
                    approval_id = self._approval.create(self._trace_id, agent_key, goal, step, tool_name, tool_params, decision.reasoning or "")
                    self._save_log(agent_key, goal, "awaiting_approval", step, tool_calls, logs, started_at)
                    if self._notifier:
                        self._notifier.notify(
                            agent_key,
                            goal,
                            "awaiting_approval",
                            (datetime.now() - datetime.fromisoformat(started_at)).total_seconds(),
                            self._cost_tracker,
                        )
                    return RuntimeResult(
                        status="awaiting_approval",
                        result=f"需要人工审批: {tool_name}",
                        iterations=step,
                        tool_calls=tool_calls,
                        logs=logs,
                        metadata={"approval_id": approval_id, "trace_id": self._trace_id, "cost": self.get_cost_usage()},
                    )

                tool_calls += 1
                tool_output_text = json.dumps(tool_result, ensure_ascii=False)
                safe_output = sanitize_tool_output(tool_output_text)
                logs.append(
                    self._make_log(
                        step,
                        "call_tool",
                        tool=tool_name,
                        params=tool_params,
                        result=safe_output,
                        duration_ms=duration_ms,
                        llm_prompt=ai_resp.get("prompt"),
                        llm_raw_response=ai_resp.get("raw_response"),
                        llm_token_usage=ai_resp.get("usage"),
                        tool_input=json.dumps(tool_params, ensure_ascii=False),
                        tool_output=tool_output_text,
                        retry_count=ai_resp.get("retry_count", 0),
                    )
                )
                messages.append(
                    {
                        "role": "assistant",
                        "content": json.dumps(decision.model_dump() if hasattr(decision, "model_dump") else decision, ensure_ascii=False),
                    }
                )
                messages.append({"role": "user", "content": f"工具返回：{safe_output}"})

                self._loop_detector.record(decision)
                loop_result = self._loop_detector.detect()
                if loop_result:
                    logs.append(
                        self._make_log(step, "loop_detected", tool=tool_name, params=tool_params, result=loop_result, duration_ms=duration_ms)
                    )
                    self._save_checkpoint(
                        agent_key,
                        goal,
                        self._make_checkpoint_state(agent_key, goal, step, messages, logs, tool_calls, context, "escalated"),
                    )
                    self._save_log(agent_key, goal, "escalated", step + 1, tool_calls, logs, started_at)
                    self._stats["total_runs"] += 1
                    self._stats["fail_count"] += 1
                    return RuntimeResult(
                        status="escalated",
                        result=f"检测到循环: {loop_result}",
                        iterations=step + 1,
                        tool_calls=tool_calls,
                        logs=logs,
                        metadata={"trace_id": self._trace_id, "cost": self.get_cost_usage()},
                    )

                self._save_checkpoint(
                    agent_key,
                    goal,
                    self._make_checkpoint_state(agent_key, goal, step, messages, logs, tool_calls, context),
                )
            else:
                logs.append(
                    self._make_log(
                        step,
                        "error",
                        tool=tool_name,
                        params=tool_params,
                        result=f"invalid action: {action}",
                        duration_ms=duration_ms,
                        llm_prompt=ai_resp.get("prompt"),
                        llm_raw_response=ai_resp.get("raw_response"),
                        llm_token_usage=ai_resp.get("usage"),
                        tool_input=None,
                        tool_output=None,
                        retry_count=ai_resp.get("retry_count", 0),
                    )
                )
                self._save_checkpoint(
                    agent_key,
                    goal,
                    self._make_checkpoint_state(agent_key, goal, step, messages, logs, tool_calls, context, "invalid"),
                )

        self._save_log(agent_key, goal, "max_iterations", max_iter, tool_calls, logs, started_at)
        if self._notifier:
            self._notifier.notify(
                agent_key, goal, "max_iterations", (datetime.now() - datetime.fromisoformat(started_at)).total_seconds(), self._cost_tracker
            )
        self._stats["total_runs"] += 1
        self._stats["fail_count"] += 1
        return RuntimeResult(
            status="max_iterations",
            result="达到最大迭代次数",
            iterations=max_iter,
            tool_calls=tool_calls,
            logs=logs,
            metadata={"trace_id": self._trace_id, "cost": self.get_cost_usage()},
        )

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

    def rollback(self, trace_id: str, target_step: int) -> dict:
        if target_step < 0:
            raise HTTPException(status_code=400, detail="step must be non-negative")
        state = self._load_runtime_snapshot(trace_id, target_step)
        if not state:
            raise HTTPException(status_code=404, detail="snapshot not found")

        agent_key = state.get("agent_key")
        goal = state.get("goal")
        if not agent_key or not goal:
            raise HTTPException(status_code=400, detail="snapshot missing agent_key or goal")

        new_trace_id = str(uuid.uuid4())
        self._trace_id = new_trace_id
        self._trace_data = list(state.get("trace") or [])
        cost = state.get("cost") or {}
        self._cost_governor.restore_usage(cost)
        self._cost_tracker = {
            "prompt_tokens": cost.get("total_input_tokens", 0),
            "completion_tokens": cost.get("total_output_tokens", 0),
            "total_tokens": cost.get("total_tokens", 0),
            "total_cost": cost.get("total_cost", 0.0),
            "step_costs": cost.get("step_costs", []),
        }

        restored_state = dict(state)
        restored_state["trace_id"] = new_trace_id
        restored_state["step"] = target_step
        restored_state["status"] = "rolled_back"
        restored_state["rolled_back_from"] = trace_id
        self._save_checkpoint(agent_key, goal, restored_state)
        result = self.execute(goal, agent_key, restored_state.get("context"))
        return {
            "trace_id": new_trace_id,
            "source_trace_id": trace_id,
            "agent_key": agent_key,
            "goal": goal,
            "step": target_step,
            "messages": restored_state.get("messages", []),
            "tool_calls_so_far": restored_state.get("tool_calls_so_far", 0),
            "cost": self.get_cost_usage(),
            "execution": result.model_dump(),
        }

    def get_status(self) -> dict:
        cur = self._agent_db.execute("SELECT status, COUNT(*) as cnt FROM agent_runtime_logs GROUP BY status")
        by_status = {r["status"]: r["cnt"] for r in cur.fetchall()}
        return {**self._stats, "by_status": by_status}

    @property
    def brain(self) -> AgentBrain:
        return self._brain

    def _reflect_before_tool(
        self,
        step: int,
        goal: str,
        agent_key: str,
        context: dict | None,
        messages: list[dict],
        decision,
        ai_resp: dict,
        llm_duration_ms: int,
        logs: list[dict],
    ) -> dict:
        """Run Reflector between LLM decision and tool execution with soft-fail protection."""
        level = self._select_reflector_level(context, llm_duration_ms)
        started = time.time()
        result = None
        reflected_params = decision.params or {}
        status = "pass"

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

        no_issue = status in {"pass", "timeout_pass", "error_pass"}
        self._update_reflector_level(level, no_issue)
        duration_ms = int((time.time() - started) * 1000)
        detail = result.detail if result is not None else status
        logger.info("Reflector level=%s result=%s detail=%s", level, status, detail)
        logs.append(
            self._make_log(
                step,
                "reflector",
                tool=decision.tool,
                params=decision.params or {},
                result={"level": level, "status": status, "detail": detail, "next_level": self._reflector_level},
                duration_ms=duration_ms,
                llm_prompt=ai_resp.get("prompt"),
                llm_raw_response=None,
                llm_token_usage=ai_resp.get("usage"),
                tool_input=json.dumps(decision.params or {}, ensure_ascii=False),
                tool_output=None,
                retry_count=ai_resp.get("retry_count", 0),
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
            return "light"
        return self._reflector_level

    def _update_reflector_level(self, level: str, no_issue: bool) -> None:
        if level != "light":
            self._reflector_light_clean_streak = 0
            return
        if not no_issue:
            self._reflector_light_clean_streak = 0
            return
        self._reflector_light_clean_streak += 1
        if self._reflector_light_clean_streak >= 3:
            self._reflector_level = "balanced"
            self._reflector_light_clean_streak = 0
