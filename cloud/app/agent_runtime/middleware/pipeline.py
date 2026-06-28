"""MiddlewarePipeline — 可插拔 middleware 链，在 Agent 核心循环前后执行。"""

from __future__ import annotations

import logging
from typing import Any

from cloud.app.agent_runtime.middleware.base import Middleware

logger = logging.getLogger(__name__)


class MiddlewarePipeline:
    def __init__(self):
        self._middlewares: list[Middleware] = []

    def register(self, middleware: Middleware) -> None:
        self._middlewares.append(middleware)
        logger.info("Middleware registered: %s", middleware.name)

    def unregister(self, name: str) -> None:
        self._middlewares = [m for m in self._middlewares if m.name != name]

    def load_for_agent(self, agent_key: str, identity: dict | None = None, middleware_names: list[str] | None = None) -> None:
        if middleware_names is None:
            return
        self._middlewares = [m for m in self._middlewares if m.name in middleware_names and m.can_handle(agent_key, identity)]

    def run_before(self, goal: str, agent_key: str, context: dict | None) -> dict | None:
        final_context = context
        for m in self._middlewares:
            result = m.before_execute(goal, agent_key, final_context)
            if result is not None:
                final_context = result
        return final_context

    def run_after(self, goal: str, agent_key: str, result: dict[str, Any]) -> dict[str, Any]:
        final_result = result
        for m in reversed(self._middlewares):
            out = m.after_execute(goal, agent_key, final_result)
            if out is not None:
                final_result = out
        return final_result

    @property
    def middlewares(self) -> list[Middleware]:
        return list(self._middlewares)
