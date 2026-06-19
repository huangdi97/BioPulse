"""Agent 执行循环 — 步骤级串行执行引擎，支持工具调用与结果收集。"""

import json
import logging
import signal
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from datetime import datetime
from typing import Any

from cloud.app.agent_runtime.agent_registry import AgentRegistry
from cloud.app.agent_runtime.agent_specs import AGENT_SPECS
from cloud.app.agent_runtime.dead_letter_queue import DeadLetterQueue
from cloud.app.agent_runtime.guard import sanitize_tool_output
from cloud.app.agent_runtime.models import RuntimeResult
from cloud.app.agent_runtime.orchestrator import Orchestrator
from cloud.app.agent_runtime.pii_redactor import PIIRedactionFilter
from cloud.app.agent_runtime.planner import PlanStep
from cloud.app.agent_runtime.runtime_llm import AllModelsFailedError
from cloud.app.agent_runtime.schema_validator import OutputSchemaValidator
from cloud.app.agent_runtime.telemetry import trace_step
from cloud.app.agent_runtime.validator import Validator


def _identity_to_spec(agent) -> dict:
    identity = agent.identity
    return {
        "role_desc": f"你是{identity.role}，{identity.goal}",
        "allowed_tools": identity.allowed_tools,
        "max_iterations": 10,
        "default_temperature": identity.model_preference.temperature,
        "max_permission": identity.safety_profile.max_permission,
        "trigger_cron": None,
        "trigger_mode": identity.trigger_mode.value,
        "event_subscriptions": identity.event_subscriptions,
    }


logger = logging.getLogger(__name__)
logger.addFilter(PIIRedactionFilter())


class OrchestratedExecution:
    def __init__(self, engine: "ExecutionEngine | None" = None):
        self._engine = engine
        self._orchestrator = Orchestrator(runtime_core=engine)

    def register_agent(self, agent_key: str, agent: Any) -> None:
        self._orchestrator.register(agent_key, agent)

    def dispatch_to_agents(self, goal: str, agent_keys: list[str]) -> list[RuntimeResult]:
        results = self._orchestrator.dispatch(goal, agent_keys)
        return [
            RuntimeResult(
                status=r.status,
                result=r.result,
                iterations=0,
                tool_calls=0,
                logs=[],
                metadata={"agent_key": r.agent_key, "confidence": r.confidence},
            )
            for r in results
        ]

    def chain_agents(self, goal: str, steps: list[str]) -> RuntimeResult:
        result = self._orchestrator.chain(goal, steps)
        return RuntimeResult(
            status=result.status,
            result=result.result,
            iterations=0,
            tool_calls=0,
            logs=[],
            metadata={"agent_key": result.agent_key, "confidence": result.confidence},
        )


class ExecutionEngine:
    MAX_LLM_CALLS = 50
    MAX_EXECUTION_SECONDS = 600
    STEP_TIMEOUT_SECONDS = 60
    _shutdown_flag = False

    def __init__(self, host, enable_orchestrator: bool = False):
        self._host = host
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._dead_letter_queue = DeadLetterQueue()
        self._timeout_count = 0
        self._orchestrated = OrchestratedExecution(engine=self) if enable_orchestrator else None
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    @property
    def orchestrator(self) -> OrchestratedExecution | None:
        return self._orchestrated

    def _signal_handler(self, sig, frame):
        logger.warning("收到信号 %s，保存 checkpoint 后关闭", sig)
        self.__class__._shutdown_flag = True
        self._save_checkpoint_on_shutdown()

    def _save_checkpoint_on_shutdown(self):
        if not hasattr(self._host, "_trace_id") or not self._host._trace_id:
            return
        try:
            state = {
                "trace_id": self._host._trace_id,
                "step": -1,
                "messages": [],
                "logs": [],
                "tool_calls_so_far": 0,
                "goal": "",
                "agent_key": "",
                "context": {},
                "status": "interrupted",
            }
            self._host._helper._save_checkpoint("", "", state)
            logger.info("Checkpoint 已保存 (trace=%s)", self._host._trace_id)
        except Exception:
            logger.exception("保存中断 checkpoint 失败")

    def _load_approved_tool(self, agent_key, goal, checkpoint):
        if not checkpoint:
            return None, None
        app = self._host._agent_db.execute(
            "SELECT tool, params FROM agent_runtime_approvals WHERE agent_key=? AND goal=? AND status='approved' ORDER BY id DESC LIMIT 1",
            (agent_key, goal),
        ).fetchone()
        return (app["tool"], json.loads(app["params"]) if app["params"] else {}) if app else (None, None)

    def _new_context(self, goal, agent_key, context, spec):
        hot_reloader = getattr(self, "_prompt_hot_reloader", None)
        if hot_reloader:
            hot_spec = hot_reloader.get_spec(agent_key)
            if hot_spec:
                spec = {**spec, **hot_spec}
        checkpoint = self._host._helper._load_checkpoint(agent_key, goal)
        plan = None
        plan_available = False
        if checkpoint:
            messages = checkpoint["messages"]
            logs = checkpoint["logs"]
            tool_calls = checkpoint["tool_calls_so_far"]
            start_step = checkpoint["step"] + 1
        else:
            tools_list = spec.get("allowed_tools", [])
            if not tools_list:
                tools_list = [t["name"] for t in self._host._tool_registry.list_tools() if t.get("name")]
            plan = self._host._planner.generate_plan(goal, tools_list, context)
            plan_available = plan is not None and bool(plan.steps) and plan.plan_confidence > 0
            plan_section = ""
            if plan_available:
                plan_lines = ["你的计划："]
                for i, step in enumerate(plan.steps, 1):
                    plan_lines.append(f"步骤{i}: {step.description} — 工具：{step.tool}")
                plan_lines.append("")
                plan_lines.append(f"当前进度：第 0 步 / 共 {len(plan.steps)} 步")
                plan_lines.append(f"完成条件：{json.dumps(plan.completion_conditions, ensure_ascii=False)}")
                plan_section = "\n".join(plan_lines) + "\n\n"
            prompt = (
                f"你是一个{spec['role_desc']}\n\n"
                f"{plan_section}"
                f"可用工具（JSON格式）：{json.dumps(self._host._tool_registry.list_tools(), ensure_ascii=False)}\n\n"
                f"当前上下文：{json.dumps(context or {}, ensure_ascii=False)}\n\n"
                '请回复JSON格式：{"action": "call_tool"|"complete"|"error", "tool": "tool_name", "params": {...}, "reasoning": "..."}'
            )
            messages, logs, tool_calls, start_step = [{"role": "system", "content": prompt}, {"role": "user", "content": goal}], [], 0, 0
        approved_tool, approved_params = self._load_approved_tool(agent_key, goal, checkpoint)
        logs.append(self._host._planner.plan(goal, agent_key, context))
        return {
            "goal": goal,
            "agent_key": agent_key,
            "context": context,
            "messages": messages,
            "logs": logs,
            "tool_calls": tool_calls,
            "start_step": start_step,
            "started_at": datetime.now().isoformat(),
            "approved_tool": approved_tool,
            "approved_params": approved_params,
            "_plan": plan,
            "_plan_step_index": 0 if plan_available else -1,
        }

    def _execute_impl(self, goal: str, agent_key: str, context: dict | None = None) -> RuntimeResult:
        agent = AgentRegistry.get(agent_key)
        if agent is not None:
            spec = _identity_to_spec(agent)
        else:
            spec = AGENT_SPECS.get(agent_key)
        if spec is None:
            return RuntimeResult(status="error", result=f"unknown agent_key: {agent_key}", iterations=0, tool_calls=0, logs=[])
        c, max_iter = self._new_context(goal, agent_key, context, spec), min(spec["max_iterations"], 15)
        start_time = time.time()
        llm_call_count = 0
        for step in range(c["start_step"], max_iter):
            if self.__class__._shutdown_flag:
                return RuntimeResult(
                    status="interrupted",
                    result="execution interrupted by shutdown signal",
                    iterations=step - c["start_step"],
                    tool_calls=c["tool_calls"],
                    logs=c["logs"],
                )
            if time.time() - start_time > self.MAX_EXECUTION_SECONDS:
                return RuntimeResult(
                    status="timeout",
                    result="execution timeout",
                    iterations=step - c["start_step"],
                    tool_calls=c["tool_calls"],
                    logs=c["logs"],
                )
            c["messages"], step_start = self._host._compress_messages(c["messages"]), time.time()
            if c["approved_tool"] and step == c["start_step"]:
                self._run_approved_tool(c, step)
                c["approved_tool"] = None
                continue
            if not self._host._core_tools._check_budget(c["messages"]):
                return self._handle_budget_exceeded(c, step, step_start)
            if c.get("_plan") and c["_plan"].steps:
                _plan = c["_plan"]
                _total = len(_plan.steps)
                _completed = c.get("_plan_step_index", 0)
                _next_desc = _plan.steps[_completed].description if _completed < _total else "全部完成"
                _last_output = ""
                for _msg in reversed(c["messages"]):
                    if isinstance(_msg.get("content"), str) and _msg["content"].startswith("工具返回："):
                        _last_output = _msg["content"][:100]
                        break
                c["messages"].append(
                    {
                        "role": "user",
                        "content": (f"当前进度：已完成步骤 {_completed}/{_total}\n上一步结果：{_last_output}\n计划中下一步：{_next_desc}"),
                    }
                )
            try:
                streamer = getattr(self, "_streamer", None)
                trace_id = getattr(self, "_trace_id", None)
                if streamer and trace_id:
                    streamer.stream(trace_id, "agent.llm_call", {"step": step, "agent": c["agent_key"]})
                future = self._executor.submit(self._host._call_ai, c["messages"], spec["default_temperature"], step, None)
                try:
                    ai_resp = future.result(timeout=self.STEP_TIMEOUT_SECONDS)
                except FuturesTimeoutError:
                    self._timeout_count += 1
                    with trace_step("llm_call_timeout", {"step": step, "agent": c["agent_key"]}):
                        pass
                    logger.warning("Step %d timed out after %ds for agent %s", step, self.STEP_TIMEOUT_SECONDS, c["agent_key"])
                    return RuntimeResult(
                        status="timeout",
                        result="Agent step timed out",
                        iterations=step - c["start_step"],
                        tool_calls=c["tool_calls"],
                        logs=c["logs"],
                    )
                llm_call_count += 1
                if llm_call_count > self.MAX_LLM_CALLS:
                    return RuntimeResult(
                        status="llm_limit_exceeded",
                        result="LLM call limit exceeded",
                        iterations=step - c["start_step"],
                        tool_calls=c["tool_calls"],
                        logs=c["logs"],
                    )
                if streamer and trace_id:
                    streamer.stream(trace_id, "agent.llm_result", {"step": step, "reply_preview": ai_resp.get("reply", "")[:200]})
                validator = OutputSchemaValidator()
                try:
                    parsed = json.loads(ai_resp.get("reply", "{}"))
                    passed, errors = validator.validate(c["agent_key"], parsed)
                    if not passed:
                        corrected = validator.coerce(c["agent_key"], parsed)
                        ai_resp["reply"] = json.dumps(corrected, ensure_ascii=False)
                        logger.warning("Schema validation for %s failed: %s; coerced output", c["agent_key"], errors)
                except (json.JSONDecodeError, TypeError):
                    logger.warning("执行循环异常", exc_info=True)
                self._host._core_tools._accumulate_cost(ai_resp, step)
            except AllModelsFailedError as exc:
                logger.error("All LLM providers failed for %s: %s", c["agent_key"], exc)
                return RuntimeResult(
                    status="llm_failed",
                    result=f"All LLM providers failed: {exc}",
                    iterations=step - c["start_step"],
                    tool_calls=c["tool_calls"],
                    logs=c["logs"],
                )
            except (KeyError, TypeError, ValueError) as exc:
                if self._host._tool_exec._handle_step_error(c, step, str(exc), duration_ms=int((time.time() - step_start) * 1000)):
                    continue
                raise
            if not self._host._core_tools._check_budget():
                return self._host._handle_budget_exceeded(c, step, step_start)
            result = self._handle_step_result(c, step, ai_resp, int((time.time() - step_start) * 1000), spec)
            if isinstance(result, RuntimeResult):
                return result
        return self._host._tool_exec._handle_max_iterations(c, max_iter)

    def _run_approved_tool(self, c, step):
        started = time.time()
        tool, params = c["approved_tool"], c["approved_params"]
        tool_result = self._host._tool_registry.call(tool, params, self._host._auth_header, caller_permission="write")
        self._host._verifier.verify(tool_result)
        if tool_result.get("needs_approval"):
            tool_result = {"success": False, "data": None, "error": "still requires approval"}
        self._record_tool_output(c, step, tool, params, tool_result, int((time.time() - started) * 1000))
        c["tool_calls"] += 1
        self._host._tool_exec._save_step_checkpoint(c, step)

    def _handle_step_result(self, c, step, ai_resp, duration_ms, spec):
        with trace_step("decide_next_action"):
            decision, error = Validator.validate(ai_resp["reply"])
            if error or decision is None:
                self._host._tool_exec._append_invalid_step(c, step, error or "invalid decision", duration_ms, ai_resp)
                return None
            tool_name, tool_params = decision.tool, decision.params or {}
            if self._host._is_completed(decision):
                return self._host._tool_exec._handle_completion(c, step, decision, ai_resp, duration_ms)
            if decision.action == "call_tool" and tool_name:
                if c.get("_plan") and c["_plan"].steps:
                    _plan = c["_plan"]
                    _plan_idx = c.get("_plan_step_index", 0)
                    if _plan_idx < len(_plan.steps):
                        _expected = _plan.steps[_plan_idx].tool
                        if tool_name != _expected:
                            logger.warning("plan deviation: expected %s, got %s for step %d", _expected, tool_name, step)
                            c["_plan_step_index"] = _plan_idx + 1
                return self._process_tool_call(c, step, tool_name, tool_params, decision, ai_resp, duration_ms, spec)
            self._host._tool_exec._append_invalid_step(c, step, f"invalid action: {decision.action}", duration_ms, ai_resp, tool_name, tool_params)
            return None

    def _process_tool_call(self, c, step, tool_name, tool_params, decision, ai_resp, duration_ms, spec):
        tool_params = self._host._tool_exec._reflect_before_tool(
            step, c["goal"], c["agent_key"], c["context"], c["messages"], decision, ai_resp, duration_ms, c["logs"]
        )
        streamer = getattr(self, "_streamer", None)
        trace_id = getattr(self, "_trace_id", None)
        if streamer and trace_id:
            streamer.stream(trace_id, "agent.tool_call", {"step": step, "tool": tool_name, "params": tool_params})
        try:
            with trace_step("tool_call", {"tool": tool_name}):
                t_start = time.time()
                tool_result = self._host._tool_registry.call(
                    tool_name, tool_params, self._host._auth_header, caller_permission=spec.get("max_permission", "read")
                )
                t_elapsed = int((time.time() - t_start) * 1000)
            if c.get("_reflection_step") != step or c.get("_reflection_tool") != tool_name:
                c["_reflection_retries"] = 0
                c["_reflection_step"] = step
                c["_reflection_tool"] = tool_name
            _plan_step = PlanStep(
                step_id=f"exec_step_{step}",
                description=getattr(decision, "reasoning", "") or "",
                tool=tool_name,
                params_template=tool_params or {},
            )
            _v_result = self._host._verifier.verify_step(_plan_step, tool_result)
            if not _v_result.passed:
                c["_reflection_retries"] = c.get("_reflection_retries", 0) + 1
                _failed = [chk for chk in _v_result.checks if not chk.passed]
                _fail_detail = "; ".join(f"{chk.name}: {chk.detail}" for chk in _failed)
                logger.warning("Reflection failed for step %s tool %s: %s", step, tool_name, _fail_detail)
                c["logs"].append(
                    {
                        "step": step,
                        "type": "reflection_failure",
                        "detail": _fail_detail,
                        "retries": c["_reflection_retries"],
                    }
                )
                if c["_reflection_retries"] < 3:
                    c["messages"].append({"role": "user", "content": f"反思反馈：上一步结果未通过验证。\n问题：{_fail_detail}\n请修正后重试。"})
                    return None
                c["messages"].append(
                    {"role": "user", "content": f"反思反馈：上一步结果未通过验证（已达最大重试次数）。\n问题：{_fail_detail}\n请谨慎继续。"}
                )
            else:
                _llm_ok = [chk for chk in _v_result.checks if chk.name == "llm_verification" and chk.passed and "Skipped" not in chk.detail]
                if _llm_ok:
                    c["messages"].append({"role": "user", "content": f"上一步结果已通过验证：{_llm_ok[0].detail}"})
            self._host._verifier.verify(tool_result)
            if streamer and trace_id:
                preview = str(tool_result.get("data", ""))[:200]
                streamer.stream(trace_id, "agent.tool_result", {"step": step, "tool": tool_name, "result_preview": preview})
            tracer = getattr(self, "_tracer", None)
            if tracer:
                tracer.log_tool_call(tool_name, tool_params, str(tool_result.get("data", "")), t_elapsed)
        except (KeyError, TypeError, ValueError) as exc:
            if not self._host._tool_exec._handle_step_error(c, step, str(exc), tool_name, tool_params, duration_ms, ai_resp):
                raise
            return None
        if tool_result.get("needs_approval"):
            return self._host._tool_exec._handle_approval_needed(c, step, tool_name, tool_params, decision)
        self._record_tool_output(c, step, tool_name, tool_params, tool_result, duration_ms, ai_resp, decision)
        c["tool_calls"] += 1
        self._host._loop_detector.record(decision)
        loop_result = self._host._loop_detector.detect()
        if loop_result:
            return self._host._tool_exec._handle_loop_detected(c, step, tool_name, tool_params, loop_result, duration_ms)
        self._host._tool_exec._save_step_checkpoint(c, step)
        return None

    def _record_tool_output(self, c, step, tool, params, tool_result, duration_ms, ai_resp=None, decision=None):
        tool_output_text = json.dumps(tool_result, ensure_ascii=False)
        safe_output = sanitize_tool_output(tool_output_text)
        c["logs"].append(
            self._host._core_tools._build_step_log(
                step,
                "call_tool",
                tool=tool,
                params=params,
                result=safe_output,
                duration_ms=duration_ms,
                **self._host._core_tools._llm_meta(ai_resp, params, tool_output_text),
            )
        )
        payload = decision.model_dump() if decision and hasattr(decision, "model_dump") else decision
        c["messages"].append(
            {"role": "assistant", "content": json.dumps(payload or {"action": "call_tool", "tool": tool, "params": params}, ensure_ascii=False)}
        )
        c["messages"].append({"role": "user", "content": f"工具返回：{safe_output}"})
        return safe_output

    def execute(self, goal: str, agent_key: str, context: dict | None = None) -> RuntimeResult:
        try:
            return self._execute_impl(goal, agent_key, context)
        except AllModelsFailedError as exc:
            logger.error("LLM degraded for %s: %s", agent_key, exc)
            self._dead_letter_queue.push(
                {
                    "agent_key": agent_key,
                    "input": goal,
                    "error": f"LLM failed: {exc}",
                    "timestamp": time.time(),
                    "retry_count": 0,
                }
            )
            return RuntimeResult(
                status="degraded",
                result=f"{agent_key} temporarily unavailable",
                iterations=0,
                tool_calls=0,
                logs=[],
            )
        except (KeyError, TypeError, ValueError, ConnectionError, TimeoutError) as exc:
            logger.error("Tool degraded for %s: %s", agent_key, exc)
            self._dead_letter_queue.push(
                {
                    "agent_key": agent_key,
                    "input": goal,
                    "error": f"Tool call failed: {exc}",
                    "timestamp": time.time(),
                    "retry_count": 0,
                }
            )
            return RuntimeResult(
                status="degraded",
                result=f"Tool {agent_key} unavailable",
                iterations=0,
                tool_calls=0,
                logs=[],
            )
        except Exception as exc:
            logger.error("Unexpected execution error for %s: %s", agent_key, exc, exc_info=True)
            self._dead_letter_queue.push(
                {
                    "agent_key": agent_key,
                    "input": goal,
                    "error": f"Unexpected error: {exc}",
                    "timestamp": time.time(),
                    "retry_count": 0,
                }
            )
            return RuntimeResult(
                status="error",
                result=f"Execution failed: {exc}",
                iterations=0,
                tool_calls=0,
                logs=[],
            )
