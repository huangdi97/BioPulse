"""AI 网关服务，统一封装对大语言模型（DeepSeek）的调用。"""

import json
import urllib.error
import urllib.request

from fastapi import HTTPException
from starlette import status

from cloud.app.services.base import BaseService
from cloud.app.services.token_budget_service import TokenBudgetService
from shared.config import settings

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
TIMEOUT_SECONDS = 30


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

    def chat(self, messages: list[dict], temperature: float, max_tokens: int, user_id: int) -> dict:
        api_key = self._get_api_key()

        req_body = {
            "model": "deepseek-chat",
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
        TokenBudgetService().record_usage(user_id, "deepseek-chat", usage.get("total_tokens", 0), cost)

        return {"reply": reply, "usage": usage}
