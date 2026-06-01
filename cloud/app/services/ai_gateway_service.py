import json
import urllib.error
import urllib.request

from fastapi import HTTPException
from starlette import status

from cloud.app.services.base import BaseService
from shared.config import settings

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
TIMEOUT_SECONDS = 30


class AiGatewayService(BaseService):
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

    def chat(self, messages: list[dict], temperature: float, max_tokens: int) -> dict:
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

        return {"reply": reply, "usage": usage}
