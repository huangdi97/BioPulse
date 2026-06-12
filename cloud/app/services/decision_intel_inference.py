"""决策推理引擎：AI 调用与 JSON 解析工具。"""

import json
import urllib.error
import urllib.request
from typing import Any

from shared.ai_gateway import LLM_INFERENCE_TIMEOUT
from shared.config import settings as config_settings


def parse_json(raw: str, default: Any = None) -> Any:
    """安全解析 JSON 字符串。"""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else raw


def call_ai(messages: list[dict], auth_header: str) -> dict:
    """调用 AI 推理接口。"""
    payload = {"messages": messages, "temperature": 0.7, "max_tokens": 2048}
    req = urllib.request.Request(
        f"{config_settings.ai_chat_url}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": auth_header},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=LLM_INFERENCE_TIMEOUT) as rp:
        return json.loads(rp.read().decode("utf-8")).get("data", {})
