"""MemoryNamespace — 基于 dict 的 lightweight 记忆命名空间。"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

__all__ = ["MemoryNamespace"]


@dataclass
class MemoryEntry:
    key: str
    value: str
    timestamp: float = field(default_factory=time.time)


class MemoryNamespace:
    """Agent 粒度的记忆命名空间，基于 dict 后端。"""

    def __init__(self, namespace: str = "") -> None:
        self._namespace = namespace
        self._store: dict[str, MemoryEntry] = {}
        self._order: list[str] = []

    @property
    def namespace(self) -> str:
        return self._namespace

    def store(self, key: str, value: str) -> None:
        entry = MemoryEntry(key=key, value=value)
        self._store[key] = entry
        if key in self._order:
            self._order.remove(key)
        self._order.append(key)

    def retrieve(self, key: str) -> str | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        return entry.value

    def search(self, query: str, k: int = 10) -> list[dict[str, Any]]:
        query_lower = query.lower()
        results: list[MemoryEntry] = []
        for entry in self._store.values():
            if query_lower in entry.key.lower() or query_lower in entry.value.lower():
                results.append(entry)
        results.sort(key=lambda e: e.timestamp, reverse=True)
        return [{"key": e.key, "value": e.value, "timestamp": e.timestamp} for e in results[:k]]

    def recent(self, n: int = 5) -> list[dict[str, Any]]:
        recent_keys = self._order[-n:]
        recent_keys.reverse()
        return [{"key": k, "value": self._store[k].value, "timestamp": self._store[k].timestamp} for k in recent_keys]

    def __len__(self) -> int:
        return len(self._store)
