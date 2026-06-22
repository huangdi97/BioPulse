"""Tool execution handlers for the runtime core — step-level error, completion, approval, and reflection."""

import concurrent.futures
import json
import logging
import time

from shared.app_settings import settings

logger = logging.getLogger(__name__)
_KEEP_CONTEXT = object()


class ToolExecutor:
    def __init__(self, host):
        self._host = host

    def execute_with_timeout(self, tool_name: str, params: dict, timeout: int | None = None, caller_agent_id: str | None = None) -> dict:
        timeout = timeout or settings.tool_timeout_seconds
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                self._host._tool_registry.call,
                tool_name,
                params,
                self._host._auth_header,
                caller_permission="write",
                trace_id=self._host._trace_id,
                caller_agent_id=caller_agent_id,
            )
            try:
                result = future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                future.cancel()
                return {"success": False, "data": None, "error": f"tool execution timed out after {timeout}s"}
        return result

    def _save_step_checkpoint(self, c, step, status="active", context=_KEEP_CONTEXT):
        context = c["context"] if context is _KEEP_CONTEXT else context
        state = self._host._helper._make_checkpoint_state(
            c["agent_key"],
            c["goal"],
            step,
            c["messages"],
            c["logs"],
            c["tool_calls"],
            context,
            status,
        )
        state_json = json.dumps(state, ensure_ascii=False, default=str)
        size_bytes = len(state_json.encode("utf-8"))
        if size_bytes > 500 * 1024:
            logger.warning("Checkpoint size %d bytes > 500KB, truncating tool return content", size_bytes)
            for msg in c["messages"]:
                if isinstance(msg.get("content"), str) and msg["content"].startswith("工具返回："):
                    msg["content"] = msg["content"][:2000] + "... [truncated]"
            state = self._host._helper._make_checkpoint_state(
                c["agent_key"],
                c["goal"],
                step,
                c["messages"],
                c["logs"],
                c["tool_calls"],
                context,
                status,
            )
        elif size_bytes > 100 * 1024:
            logger.warning("Checkpoint size %d bytes exceeds 100KB threshold", size_bytes)
        self._host._helper._save_checkpoint(
            c["agent_key"],
            c["goal"],
            state,
        )

    def _handle_step_error(self, c, step, error_msg, tool=None, params=None, duration_ms=0, ai_resp=None):
        c["logs"].append(
            self._host._core_tools._build_step_log(
                step,
                "error",
                tool=tool,
                params=params,
                result=error_msg,
                duration_ms=duration_ms,
                **self._host._core_tools._llm_meta(ai_resp, params),
            )
        )
        self._save_step_checkpoint(c, step, "failed")
        rolled = self._host._helper._try_rollback(c["agent_key"])
        if not rolled:
            return False
        c["messages"], c["logs"], c["context"] = rolled
        return True

    def _handle_completion(self, c, step, decision, ai_resp, duration_ms):
        agent_key = c.get("agent_key", "")
        try:
            import json

            output = json.loads(decision.reasoning) if isinstance(decision.reasoning, str) else decision.reasoning
            if isinstance(output, dict) and agent_key:
                self._host._verifier.verify(output, agent_key)
        except (json.JSONDecodeError, TypeError):
            pass
        except ValueError as e:
            logger.warning("Output schema validation failed for %s: %s", agent_key, e)
            return self._host._finish(c, "schema_blocked", f"Output blocked: {e}", step, step + 1, False, notify=True, delete_checkpoint=True)
        c["logs"].append(
            self._host._core_tools._build_step_log(
                step,
                "complete",
                result=decision.reasoning or "",
                duration_ms=duration_ms,
                **self._host._core_tools._llm_meta(ai_resp, include_tool_input=False),
            )
        )
        self._save_step_checkpoint(c, step, "completed")
        return self._host._finish(c, "completed", decision.reasoning or "任务完成", step, step + 1, True, notify=True, delete_checkpoint=True)

    def _handle_loop_detected(self, c, step, tool_name, tool_params, loop_result, duration_ms):
        c["logs"].append(
            self._host._core_tools._build_step_log(
                step, "loop_detected", tool=tool_name, params=tool_params, result=loop_result, duration_ms=duration_ms
            )
        )
        self._save_step_checkpoint(c, step, "escalated")
        return self._host._finish(c, "escalated", f"检测到循环: {loop_result}", step, step + 1, False)

    def _handle_approval_needed(self, c, step, tool_name, tool_params, decision):
        self._save_step_checkpoint(c, step, "awaiting_approval", context=None)
        approval_id = self._host._approval.create(
            self._host._trace_id, c["agent_key"], c["goal"], step, tool_name, tool_params, decision.reasoning or ""
        )
        return self._host._finish(
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
        return self._host._finish(c, "max_iterations", "达到最大迭代次数", max_iter - 1, max_iter, False, notify=True)

    def _append_invalid_step(self, c, step, message, duration_ms, ai_resp, tool=None, params=None):
        c["logs"].append(
            self._host._core_tools._build_step_log(
                step,
                "error",
                tool=tool,
                params=params,
                result=message,
                duration_ms=duration_ms,
                **self._host._core_tools._llm_meta(ai_resp, include_tool_input=False),
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
                "cost": self._host.get_cost_usage(),
                "llm_usage": ai_resp.get("usage"),
                "trace_id": self._host._trace_id,
            }
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            future = executor.submit(self._host._reflector.review_decision, goal, decision, review_context, level)
            try:
                result = future.result(timeout=settings.tool_timeout_seconds)
            except concurrent.futures.TimeoutError:
                future.cancel()
                status = "timeout_pass"
            finally:
                executor.shutdown(wait=False, cancel_futures=True)
        except (TimeoutError, OSError, ValueError) as exc:
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
            self._host._core_tools._build_step_log(
                step,
                "reflector",
                tool=decision.tool,
                params=decision.params or {},
                result={
                    "level": level,
                    "status": status,
                    "detail": detail,
                    "next_level": self._host._reflector_level,
                },
                duration_ms=int((time.time() - started) * 1000),
                **self._host._core_tools._llm_meta(ai_resp, decision.params or {}, include_tool_input=True),
            )
        )
        return reflected_params

    def _select_reflector_level(self, context: dict | None, llm_duration_ms: int) -> str:
        requested = (context or {}).get("reflector_level")
        if requested in {"thorough", "balanced", "light"}:
            self._host._reflector_level = requested
            return requested
        if llm_duration_ms > 5000:
            self._host._reflector_level = "light"
        return self._host._reflector_level

    def _update_reflector_level(self, level: str, no_issue: bool) -> None:
        if level != "light" or not no_issue:
            self._host._reflector_light_clean_streak = 0
            return
        self._host._reflector_light_clean_streak += 1
        if self._host._reflector_light_clean_streak >= 3:
            self._host._reflector_level = "balanced"
            self._host._reflector_light_clean_streak = 0
