"""RuntimeCore shared utility methods."""

import json


class RuntimeCoreToolsMixin:
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
        db = getattr(self, "_agent_db", None)
        if db:
            self._cost_governor.record_call(
                agent_name=getattr(self, "_trace_id", "unknown"),
                model=ai_resp.get("model_tier", "cloud_normal"),
                input_tokens=cost.get("input_tokens", 0),
                output_tokens=cost.get("output_tokens", 0),
                cost=cost.get("cost", 0.0),
                trace_id=getattr(self, "_trace_id", ""),
                db=db,
            )
