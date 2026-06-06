"""Agent 运行时 LLM 调用、Token 估算与消息压缩。"""

import json
import logging
import time
import urllib.request
from datetime import datetime
from functools import partial

from cloud.app.agent_runtime.retry import retry_with_backoff
from shared.app_settings import settings

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
            f"{settings.cloud_api_base}/ai/chat",
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": self._auth_header,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as rp:
            return json.loads(rp.read().decode("utf-8"))

    def _call_ai(self, messages: list[dict], temperature: float, step: int = 0) -> dict:
        prompt_text = json.dumps(messages, ensure_ascii=False)
        input_len = len(prompt_text)
        call_start = time.time()

        request_body = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048,
        }
        fn = partial(self._raw_llm_call, request_body)
        result = retry_with_backoff(fn, max_attempts=4, base_delay=1.0)

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
            }
        raise RuntimeError(f"LLM call failed after {result['attempts']} attempts: {result['error']}")
