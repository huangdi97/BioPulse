"""Agent 运行时 LLM 调用、Token 估算与消息压缩。"""

import json
import logging
import time
import urllib.request
from datetime import datetime
from functools import partial

from cloud.app.agent_runtime.cost_governor import CostGovernor
from cloud.app.agent_runtime.retry import retry_with_backoff
from shared.config import settings as config_settings

logger = logging.getLogger(__name__)


class RuntimeLLM:
    """提供 LLM 调用、Token 估算与消息压缩的混入类。"""

    @staticmethod
    def _estimate_token_count(messages: list[dict]) -> int:
        total = 0
        for msg in messages:
            total += len(msg.get("content", "")) // 4
            total += len(msg.get("role", "")) // 4
        return total

    def _compress_messages(self, messages: list[dict]) -> list[dict]:
        if self._estimate_token_count(messages) < 4000:
            return messages
        compressed = [m for m in messages if m["role"] == "system"]
        recent = [m for m in messages if m["role"] != "system"][-6:]
        compressed.extend(recent)
        if compressed:
            compressed[0]["content"] += f"\n\n[上下文已压缩。保留了最近{len(recent) // 2}轮对话。当前步骤：继续执行。]"
        return compressed

    def _raw_llm_call(self, request_body: dict) -> dict:
        req = urllib.request.Request(
            f"{config_settings.ai_chat_url}",
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": self._auth_header,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as rp:
            return json.loads(rp.read().decode("utf-8"))

    @staticmethod
    def _estimate_complexity(messages: list[dict]) -> int:
        total_chars = sum(len(m.get("content", "")) for m in messages)
        if total_chars < 500:
            return 1
        if total_chars < 2000:
            return 2
        if total_chars < 5000:
            return 3
        if total_chars < 10000:
            return 4
        return 5

    def _call_local(self, messages: list[dict], temperature: float) -> dict:
        prompt_text = "\n\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages)
        body = {
            "model": config_settings.ai_local_model,
            "prompt": prompt_text,
            "stream": False,
            "options": {"temperature": temperature},
        }
        req = urllib.request.Request(
            config_settings.ai_local_endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as rp:
                raw = json.loads(rp.read().decode("utf-8"))
        except Exception as e:
            logger.warning("Local model call failed, fallback to Cloud Normal: %s", e)
            result = self._call_cloud_normal(messages, temperature)
            result["model_tier"] = "cloud_normal"
            return result

        normalized = {
            "data": {
                "reply": raw.get("response", ""),
                "usage": {
                    "prompt_tokens": raw.get("prompt_eval_count", 0),
                    "completion_tokens": raw.get("eval_count", 0),
                    "total_tokens": raw.get("prompt_eval_count", 0) + raw.get("eval_count", 0),
                },
            }
        }
        return {"success": True, "data": normalized, "attempts": 1}

    def _call_cloud_normal(self, messages: list[dict], temperature: float) -> dict:
        body = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048,
        }
        fn = partial(self._raw_llm_call, body)
        return retry_with_backoff(fn, max_attempts=4, base_delay=1.0)

    def _call_cloud_agent(self, messages: list[dict], temperature: float) -> dict:
        body = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048,
            "agent_mode": True,
        }
        fn = partial(self._raw_llm_call, body)
        return retry_with_backoff(fn, max_attempts=4, base_delay=1.0)

    @staticmethod
    def _usage_from_route_result(result: dict) -> dict:
        if not result.get("success"):
            return {}
        data = result.get("data") or {}
        if "data" in data:
            return data.get("data", {}).get("usage", {}) or {}
        return data.get("usage", {}) or {}

    @staticmethod
    def _annotate_route_result(result: dict, model_tier: str) -> dict:
        tier = result.get("model_tier", model_tier)
        usage = RuntimeLLM._usage_from_route_result(result)
        input_tokens = int(usage.get("prompt_tokens", 0) or 0)
        output_tokens = int(usage.get("completion_tokens", 0) or 0)
        result["model_tier"] = tier
        result["cost"] = {
            "model_tier": tier,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": round(CostGovernor.estimate_cost(input_tokens, output_tokens, tier), 9),
        }
        return result

    def _route_call(self, messages: list[dict], temperature: float, force_level: int | None = None) -> dict:
        if force_level is not None:
            level = force_level
        elif not config_settings.ai_routing_enabled:
            return self._annotate_route_result(self._call_cloud_normal(messages, temperature), "cloud_normal")
        else:
            level = self._estimate_complexity(messages)

        if level <= 2:
            return self._annotate_route_result(self._call_local(messages, temperature), "local")
        if level == 3:
            return self._annotate_route_result(self._call_cloud_normal(messages, temperature), "cloud_normal")
        return self._annotate_route_result(self._call_cloud_agent(messages, temperature), "cloud_agent")

    def _call_ai(self, messages: list[dict], temperature: float, step: int = 0, force_level: int | None = None) -> dict:
        prompt_text = json.dumps(messages, ensure_ascii=False)
        input_len = len(prompt_text)
        call_start = time.time()

        result = self._route_call(messages, temperature, force_level)

        duration_s = round(time.time() - call_start, 3)

        if result["success"]:
            ai_response = result["data"]
            data = ai_response.get("data", {})
            raw_response = json.dumps(ai_response, ensure_ascii=False)
            output_len = len(raw_response)

            self._trace_data.append(
                {
                    "step": step,
                    "input_len": input_len,
                    "output_len": output_len,
                    "duration_s": duration_s,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return {
                "reply": data.get("reply", ""),
                "usage": data.get("usage", {}),
                "prompt": prompt_text,
                "raw_response": raw_response,
                "retry_count": result["attempts"] - 1,
                "cost": result.get("cost", {}),
                "model_tier": result.get("model_tier", "cloud_normal"),
            }
        raise RuntimeError(f"LLM call failed after {result['attempts']} attempts: {result['error']}")
