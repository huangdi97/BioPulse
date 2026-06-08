"""Agent 执行循环 — 步骤级串行执行引擎，支持工具调用与结果收集。"""

import json
import logging
import time
from datetime import datetime

from cloud.app.agent_runtime.agent_specs import AGENT_SPECS
from cloud.app.agent_runtime.guard import sanitize_tool_output
from cloud.app.agent_runtime.models import RuntimeResult
from cloud.app.agent_runtime.validator import Validator

logger = logging.getLogger(__name__)


class ExecutionLoopMixin:
    def _load_approved_tool(self, agent_key, goal, checkpoint):
        if not checkpoint:
            return None, None
        app = self._agent_db.execute(
            "SELECT tool, params FROM agent_runtime_approvals WHERE agent_key=? AND goal=? AND status='approved' ORDER BY id DESC LIMIT 1",
            (agent_key, goal),
        ).fetchone()
        return (app["tool"], json.loads(app["params"]) if app["params"] else {}) if app else (None, None)

    def _new_context(self, goal, agent_key, context, spec):
        checkpoint = self._load_checkpoint(agent_key, goal)
        if checkpoint:
            messages = checkpoint["messages"]
            logs = checkpoint["logs"]
            tool_calls = checkpoint["tool_calls_so_far"]
            start_step = checkpoint["step"] + 1
        else:
            prompt = (
                f"你是一个{spec['role_desc']}\n\n"
                f"可用工具（JSON格式）：{json.dumps(self._tool_registry.list_tools(), ensure_ascii=False)}\n\n"
                f"当前上下文：{json.dumps(context or {}, ensure_ascii=False)}\n\n"
                '请回复JSON格式：{"action": "call_tool"|"complete"|"error", "tool": "tool_name", "params": {...}, "reasoning": "..."}'
            )
            messages, logs, tool_calls, start_step = [{"role": "system", "content": prompt}, {"role": "user", "content": goal}], [], 0, 0
        approved_tool, approved_params = self._load_approved_tool(agent_key, goal, checkpoint)
        logs.append(self._planner.plan(goal, agent_key, context))
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
        }

    def _execute_impl(self, goal: str, agent_key: str, context: dict | None = None) -> RuntimeResult:
        spec = AGENT_SPECS.get(agent_key)
        if spec is None:
            return RuntimeResult(status="error", result=f"unknown agent_key: {agent_key}", iterations=0, tool_calls=0, logs=[])
        c, max_iter = self._new_context(goal, agent_key, context, spec), min(spec["max_iterations"], 15)
        for step in range(c["start_step"], max_iter):
            c["messages"], step_start = self._compress_messages(c["messages"]), time.time()
            if c["approved_tool"] and step == c["start_step"]:
                self._run_approved_tool(c, step)
                c["approved_tool"] = None
                continue
            if not self._check_budget(c["messages"]):
                return self._handle_budget_exceeded(c, step, step_start)
            try:
                ai_resp = self._call_ai(c["messages"], spec["default_temperature"], step, force_level=None)
                self._accumulate_cost(ai_resp, step)
            except Exception as exc:
                if self._handle_step_error(c, step, str(exc), duration_ms=int((time.time() - step_start) * 1000)):
                    continue
                raise
            if not self._check_budget():
                return self._handle_budget_exceeded(c, step, step_start)
            result = self._handle_step_result(c, step, ai_resp, int((time.time() - step_start) * 1000), spec)
            if isinstance(result, RuntimeResult):
                return result
        return self._handle_max_iterations(c, max_iter)

    def _run_approved_tool(self, c, step):
        started = time.time()
        tool, params = c["approved_tool"], c["approved_params"]
        tool_result = self._tool_registry.call(tool, params, self._auth_header, caller_permission="write")
        self._verifier.verify(tool_result)
        if tool_result.get("needs_approval"):
            tool_result = {"success": False, "data": None, "error": "still requires approval"}
        self._record_tool_output(c, step, tool, params, tool_result, int((time.time() - started) * 1000))
        c["tool_calls"] += 1
        self._save_step_checkpoint(c, step)

    def _handle_step_result(self, c, step, ai_resp, duration_ms, spec):
        decision, error = Validator.validate(ai_resp["reply"])
        if error or decision is None:
            self._append_invalid_step(c, step, error or "invalid decision", duration_ms, ai_resp)
            return None
        tool_name, tool_params = decision.tool, decision.params or {}
        if self._is_completed(decision):
            return self._handle_completion(c, step, decision, ai_resp, duration_ms)
        if decision.action == "call_tool" and tool_name:
            return self._process_tool_call(c, step, tool_name, tool_params, decision, ai_resp, duration_ms, spec)
        self._append_invalid_step(c, step, f"invalid action: {decision.action}", duration_ms, ai_resp, tool_name, tool_params)
        return None

    def _process_tool_call(self, c, step, tool_name, tool_params, decision, ai_resp, duration_ms, spec):
        tool_params = self._reflect_before_tool(
            step, c["goal"], c["agent_key"], c["context"], c["messages"], decision, ai_resp, duration_ms, c["logs"]
        )
        try:
            tool_result = self._tool_registry.call(tool_name, tool_params, self._auth_header, caller_permission=spec.get("max_permission", "read"))
            self._verifier.verify(tool_result)
        except Exception as exc:
            if not self._handle_step_error(c, step, str(exc), tool_name, tool_params, duration_ms, ai_resp):
                raise
            return None
        if tool_result.get("needs_approval"):
            return self._handle_approval_needed(c, step, tool_name, tool_params, decision)
        self._record_tool_output(c, step, tool_name, tool_params, tool_result, duration_ms, ai_resp, decision)
        c["tool_calls"] += 1
        self._loop_detector.record(decision)
        loop_result = self._loop_detector.detect()
        if loop_result:
            return self._handle_loop_detected(c, step, tool_name, tool_params, loop_result, duration_ms)
        self._save_step_checkpoint(c, step)
        return None

    def _record_tool_output(self, c, step, tool, params, tool_result, duration_ms, ai_resp=None, decision=None):
        tool_output_text = json.dumps(tool_result, ensure_ascii=False)
        safe_output = sanitize_tool_output(tool_output_text)
        c["logs"].append(
            self._build_step_log(
                step,
                "call_tool",
                tool=tool,
                params=params,
                result=safe_output,
                duration_ms=duration_ms,
                **self._llm_meta(ai_resp, params, tool_output_text),
            )
        )
        payload = decision.model_dump() if decision and hasattr(decision, "model_dump") else decision
        c["messages"].append(
            {"role": "assistant", "content": json.dumps(payload or {"action": "call_tool", "tool": tool, "params": params}, ensure_ascii=False)}
        )
        c["messages"].append({"role": "user", "content": f"工具返回：{safe_output}"})
        return safe_output
