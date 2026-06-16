"""LLM configuration, constants, token estimation, and message compression."""

import logging

from shared.config import settings as config_settings

logger = logging.getLogger(__name__)


class AllModelsFailedError(RuntimeError):
    def __init__(self, errors: list[dict]):
        self.errors = errors
        super().__init__(f"All fallback models failed: {len(errors)} errors")


def get_fallback_chain() -> list[dict]:
    """get fallback chain."""
    return [
        {"provider": "deepseek", "model": config_settings.deepseek_model, "env_key": "DEEPSEEK_API_KEY", "url": config_settings.deepseek_api_url},
        {
            "provider": "openrouter",
            "model": config_settings.openrouter_model,
            "env_key": "OPENROUTER_API_KEY",
            "url": config_settings.openrouter_api_url,
        },
        {"provider": "openai", "model": config_settings.openai_model, "env_key": "OPENAI_API_KEY", "url": config_settings.openai_api_url},
    ]


def estimate_token_count(messages: list[dict]) -> int:
    """estimate token count."""
    total = 0
    for msg in messages:
        total += len(msg.get("content", "")) // 4
        total += len(msg.get("role", "")) // 4
    return total


def compress_messages(messages: list[dict]) -> list[dict]:
    """compress messages."""
    if estimate_token_count(messages) < 4000:
        return messages
    compressed = [m for m in messages if m["role"] == "system"]
    recent = [m for m in messages if m["role"] != "system"][-6:]
    compressed.extend(recent)
    if compressed:
        compressed[0]["content"] += f"\n\n[上下文已压缩。保留了最近{len(recent) // 2}轮对话。当前步骤：继续执行。]"
    return compressed


def estimate_complexity(messages: list[dict]) -> int:
    """estimate complexity."""
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
