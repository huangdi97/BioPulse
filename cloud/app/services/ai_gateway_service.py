"""AI 网关服务，统一封装对大语言模型（DeepSeek）的调用。"""

import json
import logging
import math
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

from fastapi import HTTPException
from starlette import status

from cloud.app.services.token_budget_service import TokenBudgetService
from shared.base_service import BaseService
from shared.config import settings

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
TIMEOUT_SECONDS = 30

_semantic_cache = None


class AiGatewayService(BaseService):
    """AI 网关服务，负责调用 DeepSeek API 并记录 Token 用量。"""

    def _get_api_key(self) -> str:
        key = settings.deepseek_api_key
        if not key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="DEEPSEEK_API_KEY not configured",
            )
        return key

    def _extract_reply(self, payload: dict) -> str:
        choices = payload.get("choices", [])
        if not choices:
            return ""
        message = choices[0].get("message", {})
        return message.get("content", "")

    def _select_model(self, messages: list[dict]) -> str:
        total_chars = sum(len(m.get("content", "")) for m in messages)
        complex_keywords = ["分析", "评估", "推理", "比较", "生成报告"]
        has_complex_keyword = any(keyword in " ".join(m.get("content", "") for m in messages) for keyword in complex_keywords)
        if total_chars < 200 and not has_complex_keyword:
            return "deepseek-chat"
        return "deepseek-chat"

    def chat(self, messages: list[dict], temperature: float, max_tokens: int, user_id: int, model_override: str | None = None) -> dict:
        global _semantic_cache
        if _semantic_cache is None:
            from cloud.app.services.semantic_cache_service import SemanticCache

            _semantic_cache = SemanticCache()

        last_msg = messages[-1] if messages else {}
        if last_msg.get("role") == "user" and len(last_msg.get("content", "")) < 500:
            cached = _semantic_cache.get(last_msg["content"])
            if cached is not None:
                return cached

        api_key = self._get_api_key()

        model = model_override if model_override else self._select_model(messages)

        req_body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        req_data = json.dumps(req_body).encode("utf-8")

        req = urllib.request.Request(
            DEEPSEEK_URL,
            data=req_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                raw = resp.read()
        except urllib.error.URLError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"DeepSeek API call failed: {exc}",
            )

        payload = json.loads(raw)
        reply = self._extract_reply(payload)
        usage = payload.get("usage", {})

        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        cost = prompt_tokens * 0.14 / 1e6 + completion_tokens * 0.28 / 1e6
        TokenBudgetService().record_usage(user_id, model, usage.get("total_tokens", 0), cost)

        result = {"reply": reply, "usage": usage}

        if last_msg.get("role") == "user" and len(last_msg.get("content", "")) < 500:
            _semantic_cache.set(last_msg["content"], result)

        return result


EMBEDDING_DIM = 128


def get_embedding(text: str) -> list[float] | None:
    try:
        vec = [0.0] * EMBEDDING_DIM
        for i in range(len(text) - 2):
            trigram = text[i : i + 3]
            h = hash(trigram) % EMBEDDING_DIM
            vec[h] += 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec
    except Exception:  # noqa: BLE001  # trigram hash / math operations have multiple failure modes
        logger.exception("get_embedding failed")
        return None
