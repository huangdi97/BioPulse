"""HITLMiddleware — 关键工具调用前检查是否需要人工审批。"""

from __future__ import annotations

import logging
from typing import Any

from cloud.app.agent_runtime.middleware.base import Middleware

logger = logging.getLogger(__name__)

_SENSITIVE_TOOLS = frozenset(
    {
        "agent_brain_delete",
        "agent_brain_set",
    }
)


class HITLMiddleware(Middleware):
    name = "hitl"

    def __init__(self, approval_queue: Any | None = None):
        self._approval_queue = approval_queue

    def before_execute(self, goal: str, agent_key: str, context: dict | None) -> dict | None:
        return context

    def after_execute(self, goal: str, agent_key: str, result: dict[str, Any]) -> dict[str, Any] | None:
        tool_name = result.get("tool", "")
        if tool_name in _SENSITIVE_TOOLS or result.get("needs_approval"):
            result["requires_hitl"] = True
            logger.info("HITLMiddleware: %s requires human approval (tool=%s)", agent_key, tool_name)
        return result
