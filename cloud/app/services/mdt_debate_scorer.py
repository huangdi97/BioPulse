"""Debate scoring and AI response parsing for MDT debate engine."""

import json
import urllib.request

from shared.ai_gateway import LLM_INFERENCE_TIMEOUT
from shared.config import settings as config_settings


def _call_ai(messages: list[dict], auth_header: str) -> dict:
    """调用 AI 网关进行辩论评分。"""
    with urllib.request.urlopen(
        urllib.request.Request(
            f"{config_settings.ai_chat_url}",
            data=json.dumps({"messages": messages, "temperature": 0.7, "max_tokens": 2048}).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": auth_header},
            method="POST",
        ),
        timeout=LLM_INFERENCE_TIMEOUT,
    ) as rp:
        return json.loads(rp.read().decode("utf-8")).get("data", {})


def _parse_json(raw: str, default=None):
    """安全解析 JSON 字符串，失败返回默认值。"""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else raw


def parse_ai_opinion(reply: str) -> dict:
    """解析 AI 回复中的辩论观点。"""
    parsed = _parse_json(reply, {})
    if isinstance(parsed, dict):
        return {
            "opinion": parsed.get("opinion", reply),
            "summary": parsed.get("summary", ""),
            "sentiment": parsed.get("sentiment", "neutral"),
            "confidence": float(parsed.get("confidence", 0.5)),
            "key_points": json.dumps(parsed.get("key_points", []), ensure_ascii=False),
        }
    return {
        "opinion": reply,
        "summary": "",
        "sentiment": "neutral",
        "confidence": 0.5,
        "key_points": "[]",
    }


def parse_consensus_json(raw: str | None) -> dict:
    """解析共识结果的 JSON 字符串。"""
    if not raw:
        return {}
    try:
        return json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return {}
