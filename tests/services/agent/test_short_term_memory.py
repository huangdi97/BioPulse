"""短期记忆（工作记忆）测试。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest


@dataclass
class Message:
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Message):
            return NotImplemented
        return self.role == other.role and self.content == other.content and self.metadata == other.metadata


VALID_ROLES = {"user", "assistant", "tool"}


class ShortTermMemory:
    def __init__(self, max_window: int = 10):
        self._messages: list[Message] = []
        self._max_window = max_window

    def append(self, role: str, content: str, metadata: dict[str, Any] | None = None) -> Message:
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role: {role}")
        msg = Message(role=role, content=content, metadata=metadata or {})
        self._messages.append(msg)
        if len(self._messages) > self._max_window:
            self._messages.pop(0)
        return msg

    def get_context(self, n: int | None = None) -> list[Message]:
        if n is None:
            n = self._max_window
        return self._messages[-n:] if self._messages else []

    def clear(self) -> None:
        self._messages.clear()

    @property
    def max_window(self) -> int:
        return self._max_window

    @max_window.setter
    def max_window(self, value: int) -> None:
        if value < 1:
            raise ValueError("max_window must be >= 1")
        self._max_window = value
        while len(self._messages) > self._max_window:
            self._messages.pop(0)

    @property
    def count(self) -> int:
        return len(self._messages)

    def __len__(self) -> int:
        return len(self._messages)


@pytest.fixture
def working_memory() -> ShortTermMemory:
    return ShortTermMemory(max_window=5)


class TestMessageAppend:
    def test_append_returns_message(self, working_memory: ShortTermMemory) -> None:
        msg = working_memory.append("user", "hello")
        assert isinstance(msg, Message)
        assert msg.role == "user"
        assert msg.content == "hello"

    def test_append_preserves_order_fifo(self, working_memory: ShortTermMemory) -> None:
        working_memory.append("user", "first")
        working_memory.append("assistant", "second")
        working_memory.append("user", "third")
        context = working_memory.get_context()
        assert [m.content for m in context] == ["first", "second", "third"]

    def test_append_with_metadata(self, working_memory: ShortTermMemory) -> None:
        msg = working_memory.append("tool", "result", {"tool_name": "search", "duration_ms": 150})
        assert msg.metadata["tool_name"] == "search"
        assert msg.metadata["duration_ms"] == 150


class TestWindowSize:
    def test_exceeds_max_window_evicts_oldest(self, working_memory: ShortTermMemory) -> None:
        for i in range(6):
            working_memory.append("user", str(i))
        context = working_memory.get_context()
        assert len(context) == 5
        assert context[0].content == "1"
        assert context[-1].content == "5"

    def test_fifo_eviction_order(self, working_memory: ShortTermMemory) -> None:
        for i in range(10):
            working_memory.append("user", str(i))
        context = working_memory.get_context()
        assert context[0].content == "5"

    def test_single_message_window(self) -> None:
        m = ShortTermMemory(max_window=1)
        m.append("user", "first")
        m.append("assistant", "second")
        assert m.count == 1
        assert m.get_context()[0].content == "second"


class TestGetContext:
    def test_get_context_returns_recent_n(self, working_memory: ShortTermMemory) -> None:
        for i in range(5):
            working_memory.append("user", str(i))
        ctx = working_memory.get_context(3)
        assert len(ctx) == 3
        assert [m.content for m in ctx] == ["2", "3", "4"]

    def test_get_context_defaults_to_max_window(self, working_memory: ShortTermMemory) -> None:
        for i in range(3):
            working_memory.append("user", str(i))
        ctx = working_memory.get_context()
        assert len(ctx) == 3

    def test_get_context_with_n_larger_than_count(self, working_memory: ShortTermMemory) -> None:
        working_memory.append("user", "only")
        ctx = working_memory.get_context(100)
        assert len(ctx) == 1


class TestMessageTypeFilter:
    def test_keeps_user_assistant_tool_only(self, working_memory: ShortTermMemory) -> None:
        working_memory.append("user", "hi")
        working_memory.append("assistant", "hello")
        working_memory.append("tool", "result")
        assert all(m.role in VALID_ROLES for m in working_memory.get_context())

    def test_rejects_invalid_role(self, working_memory: ShortTermMemory) -> None:
        with pytest.raises(ValueError):
            working_memory.append("system", "invalid role")


class TestClear:
    def test_clear_returns_empty(self, working_memory: ShortTermMemory) -> None:
        working_memory.append("user", "temp")
        working_memory.clear()
        assert working_memory.count == 0

    def test_clear_then_append_works(self, working_memory: ShortTermMemory) -> None:
        working_memory.append("user", "a")
        working_memory.append("user", "b")
        working_memory.clear()
        working_memory.append("user", "c")
        assert working_memory.count == 1
        assert working_memory.get_context()[0].content == "c"

    def test_clear_empty_is_noop(self, working_memory: ShortTermMemory) -> None:
        working_memory.clear()
        assert working_memory.count == 0


class TestAdaptiveWindow:
    def test_increase_window_preserves_all(self, working_memory: ShortTermMemory) -> None:
        for i in range(5):
            working_memory.append("user", str(i))
        working_memory.max_window = 10
        assert working_memory.count == 5

    def test_decrease_window_evicts_oldest(self, working_memory: ShortTermMemory) -> None:
        for i in range(5):
            working_memory.append("user", str(i))
        working_memory.max_window = 3
        assert working_memory.count == 3
        assert [m.content for m in working_memory.get_context()] == ["2", "3", "4"]

    def test_invalid_window_raises(self, working_memory: ShortTermMemory) -> None:
        with pytest.raises(ValueError, match="max_window must be >= 1"):
            working_memory.max_window = 0

    def test_window_property_reflects_change(self, working_memory: ShortTermMemory) -> None:
        working_memory.max_window = 20
        assert working_memory.max_window == 20


class TestEmptyMemory:
    def test_get_context_returns_empty(self, working_memory: ShortTermMemory) -> None:
        assert working_memory.get_context() == []

    def test_get_context_with_n_returns_empty(self, working_memory: ShortTermMemory) -> None:
        assert working_memory.get_context(5) == []

    def test_count_zero(self, working_memory: ShortTermMemory) -> None:
        assert working_memory.count == 0


class TestSingleMessageBoundary:
    def test_single_message_append(self) -> None:
        m = ShortTermMemory(max_window=1)
        m.append("user", "only one")
        ctx = m.get_context()
        assert len(ctx) == 1
        assert ctx[0].content == "only one"

    def test_single_message_get_context_returns_it(self) -> None:
        m = ShortTermMemory(max_window=1)
        m.append("user", "single")
        assert m.get_context(1)[0].content == "single"

    def test_single_message_replaced_by_new(self) -> None:
        m = ShortTermMemory(max_window=1)
        m.append("user", "old")
        m.append("assistant", "new")
        ctx = m.get_context()
        assert len(ctx) == 1
        assert ctx[0].content == "new"
