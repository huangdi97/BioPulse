"""Unified AI Gateway HTTP client for all services."""

import json
import logging
import urllib.request
from typing import Any

from shared.app_settings import settings

AI_GATEWAY_URL = f"{settings.cloud_api_base}/ai/chat"
TIMEOUT_SECONDS = 30
logger = logging.getLogger(__name__)


def call_ai_gateway(
    auth_header: str,
    system_prompt: str,
    user_message: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    """Call the Cloud AI Gateway with a system prompt and user message.

    Args:
        auth_header: Authorization header value.
        system_prompt: System-level instruction for the AI.
        user_message: User message content.
        temperature: Sampling temperature (default 0.7).
        max_tokens: Maximum tokens in the response (default 2048).

    Returns:
        The ``data`` envelope from the gateway response.
    """
    req_body = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    req_data = json.dumps(req_body).encode("utf-8")
    req = urllib.request.Request(
        AI_GATEWAY_URL,
        data=req_data,
        headers={
            "Content-Type": "application/json",
            "Authorization": auth_header,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        raw = resp.read()
    envelope = json.loads(raw)
    return envelope.get("data", {})
