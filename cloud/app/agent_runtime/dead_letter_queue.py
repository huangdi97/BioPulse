"""死信队列 — 无法处理的请求持久化存储，支持重试。"""

import time
from typing import Any


class DeadLetterEntry:
    def __init__(self, agent_key: str, input_data: str, error: str, timestamp: float | None = None, retry_count: int = 0):
        self.agent_key = agent_key
        self.input = input_data
        self.error = error
        self.timestamp = timestamp or time.time()
        self.retry_count = retry_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_key": self.agent_key,
            "input": self.input,
            "error": self.error,
            "timestamp": self.timestamp,
            "retry_count": self.retry_count,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "DeadLetterEntry":
        return cls(
            agent_key=d["agent_key"],
            input_data=d["input"],
            error=d["error"],
            timestamp=d.get("timestamp", time.time()),
            retry_count=d.get("retry_count", 0),
        )


class DeadLetterQueue:
    def __init__(self):
        self._entries: list[DeadLetterEntry] = []

    def push(self, entry: dict[str, Any] | DeadLetterEntry) -> None:
        if isinstance(entry, dict):
            entry = DeadLetterEntry.from_dict(entry)
        self._entries.append(entry)

    def pop_all(self) -> list[dict[str, Any]]:
        result = [e.to_dict() for e in self._entries]
        self._entries.clear()
        return result

    def retry(self, entry: dict[str, Any] | DeadLetterEntry, max_retries: int = 3) -> bool:
        if isinstance(entry, dict):
            entry = DeadLetterEntry.from_dict(entry)
        if entry.retry_count >= max_retries:
            return False
        entry.retry_count += 1
        return True

    def __len__(self) -> int:
        return len(self._entries)
