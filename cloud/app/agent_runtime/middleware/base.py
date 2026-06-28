"""Middleware 基类 — 所有 Agent 运行时中间件的抽象基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Middleware(ABC):
    name: str = "base"

    @abstractmethod
    def before_execute(self, goal: str, agent_key: str, context: dict | None) -> dict | None: ...

    @abstractmethod
    def after_execute(self, goal: str, agent_key: str, result: dict[str, Any]) -> dict[str, Any] | None: ...

    def can_handle(self, agent_key: str, identity: dict | None = None) -> bool:
        return True
