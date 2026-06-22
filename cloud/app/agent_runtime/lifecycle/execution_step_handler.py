"""执行步骤处理器 — 处理步骤结果、审批工具执行、工具调用处理。"""

import json
import logging
import time

from cloud.app.agent_runtime.comm.telemetry import trace_step
from cloud.app.agent_runtime.core.planner import PlanStep
from cloud.app.agent_runtime.safety.completion_verifier import CompletionVerifier
from cloud.app.agent_runtime.safety.guard import sanitize_tool_output
from cloud.app.agent_runtime.safety.pii_redactor import PIIRedactionFilter
from cloud.app.agent_runtime.safety.validator import Validator

logger = logging.getLogger(__name__)
logger.addFilter(PIIRedactionFilter())


class StepHandler:
    """Handles step-level execution: tool calls, step result processing, and reflection."""

    def __init__(self, host):
        self._host = host
        self._completion_verifier = CompletionVerifier(self._host)

    def _run_approved_tool(self, c, step):
        started = time.time()
        tool, params = c["approved_tool"], c["approved_params"]
        tool_result = self._host._tool_registry.call(
            tool, params, self._host._auth_header, caller_permission="write", trace_id=self._host._trace_id, caller_agent_id=c.get("agent_key")
        )
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
                result = self._completion_verifier.verify_and_handle(c, step, decision, ai_resp, duration_ms)
                if result is not None:
                    return result
                return None
            if decision.action == "call_tool" and tool_name:
                if c.get("_plan") and c["_plan"].steps:
                    _plan = c["_plan"]
                    _plan_idx = c.get("_plan_step_index", 0)
                    if _plan_idx < len(_plan.steps):
                        _expected = _plan.steps[_plan_idx].tool
                        if tool_name != _expected:
                            logger.warning("plan deviation: expected %s, got %s for step %d", _expected, tool_name, step)
                            c["_plan_deviation_count"] = c.get("_plan_deviation_count", 0) + 1
                            c["_plan_step_index"] = _plan_idx + 1
                return self._process_tool_call(c, step, tool_name, tool_params, decision, ai_resp, duration_ms, spec)
            self._host._tool_exec._append_invalid_step(c, step, f"invalid action: {decision.action}", duration_ms, ai_resp, tool_name, tool_params)
            return None

    def _handle_reflection_result(self, c, step, tool_name, tool_params, decision, tool_result) -> bool:
        """Handle reflection verification. Returns True if caller should short-circuit (return None)."""
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
            c["logs"].append({"step": step, "type": "reflection_failure", "detail": _fail_detail, "retries": c["_reflection_retries"]})
            if c["_reflection_retries"] < 3:
                c["messages"].append({"role": "user", "content": f"反思反馈：上一步结果未通过验证。\n问题：{_fail_detail}\n请修正后重试。"})
                return True
            c["messages"].append(
                {"role": "user", "content": f"反思反馈：上一步结果未通过验证（已达最大重试次数）。\n问题：{_fail_detail}\n请谨慎继续。"}
            )
        else:
            _llm_ok = [chk for chk in _v_result.checks if chk.name == "llm_verification" and chk.passed and "Skipped" not in chk.detail]
            if _llm_ok:
                c["messages"].append({"role": "user", "content": f"上一步结果已通过验证：{_llm_ok[0].detail}"})
        return False

    def _process_tool_call(self, c, step, tool_name, tool_params, decision, ai_resp, duration_ms, spec):
        tool_params = self._host._tool_exec._reflect_before_tool(
            step, c["goal"], c["agent_key"], c["context"], c["messages"], decision, ai_resp, duration_ms, c["logs"]
        )
        streamer = getattr(self._host, "_streamer", None)
        trace_id = getattr(self._host, "_trace_id", None)
        if streamer and trace_id:
            streamer.stream(trace_id, "agent.tool_call", {"step": step, "tool": tool_name, "params": tool_params})
        try:
            with trace_step("tool_call", {"tool": tool_name}):
                t_start = time.time()
                tool_result = self._host._tool_registry.call(
                    tool_name,
                    tool_params,
                    self._host._auth_header,
                    caller_permission=spec.get("max_permission", "read"),
                    trace_id=self._host._trace_id,
                    caller_agent_id=c.get("agent_key"),
                )
                t_elapsed = int((time.time() - t_start) * 1000)
            if self._handle_reflection_result(c, step, tool_name, tool_params, decision, tool_result):
                return None
            self._host._verifier.verify(tool_result)
            if streamer and trace_id:
                preview = str(tool_result.get("data", ""))[:200]
                streamer.stream(trace_id, "agent.tool_result", {"step": step, "tool": tool_name, "result_preview": preview})
            tracer = getattr(self._host, "_tracer", None)
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
