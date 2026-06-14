"""MemoryService — 管理 Agent 粒度的记忆命名空间。"""

from __future__ import annotations

from cloud.app.services.memory_namespace import MemoryNamespace

__all__ = ["MemoryService"]


class MemoryService:
    """记忆服务，管理多个 Agent 的 MemoryNamespace。"""

    def __init__(self) -> None:
        self._namespaces: dict[str, MemoryNamespace] = {}

    def get_namespace(self, agent_id: str) -> MemoryNamespace:
        if agent_id not in self._namespaces:
            self._namespaces[agent_id] = MemoryNamespace(namespace=agent_id)
        return self._namespaces[agent_id]
