"""工具桥接工具函数：幂等性、错误格式化、结果类型。"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    """Dataclass representing the result of a tool execution."""

    success: bool = False
    data: Any = None
    error: str = ""


def idempotency_key(agent_key: str, trace_id: str, step: int) -> str:
    """Generate a UUID-based idempotency key from agent_key, trace_id, and step."""
    raw = f"{agent_key}:{trace_id}:{step}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, raw))


def check_idempotency(cache: dict, key: str, ttl: float) -> Any | None:
    """Check if a cached idempotent result exists and is still within TTL."""
    now = time.time()
    entry = cache.get(key)
    if entry is None:
        return None
    cached_time, cached_result = entry
    if now - cached_time > ttl:
        del cache[key]
        return None
    return cached_result


def set_idempotency(cache: dict, key: str, result: Any) -> None:
    """Cache a result under the given idempotency key with the current timestamp."""
    cache[key] = (time.time(), result)


def format_error(error: str) -> dict:
    """Return a standard error response dict with success=False and the error message."""
    return {
        "success": False,
        "data": None,
        "error": error,
        "needs_approval": False,
    }
