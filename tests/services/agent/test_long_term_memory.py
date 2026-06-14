"""长期记忆系统测试。"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import pytest


class MemoryNotFoundError(Exception):
    pass


@dataclass
class MemoryItem:
    id: str
    content: str
    keywords: list[str] = field(default_factory=list)
    importance: float = 0.0
    created_at: float = field(default_factory=time.time)
    merged: bool = False


class LongTermMemory:
    def __init__(self, max_items: int = 100):
        self._store: dict[str, MemoryItem] = {}
        self._max_items = max_items

    def store(self, content: str, keywords: list[str] | None = None, importance: float = 0.0) -> str:
        mem_id = f"mem_{len(self._store) + 1}_{int(time.time() * 1000)}"
        self._store[mem_id] = MemoryItem(
            id=mem_id,
            content=content,
            keywords=keywords or [],
            importance=importance,
        )
        self._enforce_capacity()
        return mem_id

    def retrieve(self, mem_id: str) -> MemoryItem:
        if mem_id not in self._store:
            raise MemoryNotFoundError(f"Memory {mem_id} not found")
        return self._store[mem_id]

    def search_by_keyword(self, keyword: str) -> list[MemoryItem]:
        return [m for m in self._store.values() if keyword in m.keywords]

    def search_semantic(self, query: str) -> list[tuple[MemoryItem, float]]:
        query_words = set(query.lower().split())
        scored = []
        for m in self._store.values():
            content_words = set(m.content.lower().split())
            kw_words = set(k.lower() for k in m.keywords)
            overlap = len(query_words & (content_words | kw_words))
            if overlap > 0:
                score = overlap / max(len(query_words), 1)
                scored.append((m, round(score, 4)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def forget(self, mem_id: str) -> None:
        self._store.pop(mem_id, None)

    def forget_by_age(self, max_age: float) -> int:
        now = time.time()
        to_delete = [mid for mid, m in self._store.items() if now - m.created_at > max_age]
        for mid in to_delete:
            del self._store[mid]
        return len(to_delete)

    def merge(self, mem_id_a: str, mem_id_b: str) -> MemoryItem:
        a = self.retrieve(mem_id_a)
        b = self.retrieve(mem_id_b)
        merged_id = f"mem_merged_{int(time.time() * 1000)}"
        merged = MemoryItem(
            id=merged_id,
            content=f"{a.content} | {b.content}",
            keywords=list(set(a.keywords + b.keywords)),
            importance=max(a.importance, b.importance),
            merged=True,
        )
        self._store[merged_id] = merged
        del self._store[mem_id_a]
        del self._store[mem_id_b]
        self._enforce_capacity()
        return merged

    def list_by_importance(self, limit: int = 10) -> list[MemoryItem]:
        sorted_items = sorted(self._store.values(), key=lambda m: m.importance, reverse=True)
        return sorted_items[:limit]

    def _enforce_capacity(self) -> None:
        if len(self._store) > self._max_items:
            sorted_items = sorted(self._store.values(), key=lambda m: m.importance)
            excess = len(self._store) - self._max_items
            for m in sorted_items[:excess]:
                del self._store[m.id]

    def clear(self) -> None:
        self._store.clear()

    @property
    def count(self) -> int:
        return len(self._store)


@pytest.fixture
def memory() -> LongTermMemory:
    return LongTermMemory(max_items=10)


class TestMemoryStore:
    def test_store_returns_memory_id(self, memory: LongTermMemory) -> None:
        mem_id = memory.store("hello world")
        assert mem_id.startswith("mem_")

    def test_store_content_is_preserved(self, memory: LongTermMemory) -> None:
        mem_id = memory.store("important data", keywords=["key"], importance=0.8)
        item = memory.retrieve(mem_id)
        assert item.content == "important data"
        assert item.keywords == ["key"]
        assert item.importance == 0.8

    def test_store_multiple_items(self, memory: LongTermMemory) -> None:
        id1 = memory.store("first")
        id2 = memory.store("second")
        id3 = memory.store("third")
        assert memory.count == 3
        assert memory.retrieve(id1).content == "first"
        assert memory.retrieve(id2).content == "second"
        assert memory.retrieve(id3).content == "third"


class TestMemoryRetrieve:
    def test_retrieve_by_id(self, memory: LongTermMemory) -> None:
        mem_id = memory.store("find me")
        result = memory.retrieve(mem_id)
        assert result.id == mem_id
        assert result.content == "find me"

    def test_retrieve_by_keyword(self, memory: LongTermMemory) -> None:
        memory.store("data science", keywords=["ml", "ai"], importance=0.9)
        memory.store("web dev", keywords=["react", "css"], importance=0.5)
        results = memory.search_by_keyword("ml")
        assert len(results) == 1
        assert results[0].content == "data science"

    def test_retrieve_semantic_by_overlap(self, memory: LongTermMemory) -> None:
        memory.store("machine learning is fun", keywords=["ml"])
        memory.store("i like pizza", keywords=["food"])
        results = memory.search_semantic("machine learning")
        assert len(results) == 1
        assert results[0][0].content == "machine learning is fun"

    def test_retrieve_invalid_id_raises_error(self, memory: LongTermMemory) -> None:
        with pytest.raises(MemoryNotFoundError, match="not found"):
            memory.retrieve("nonexistent_id")


class TestMemoryForget:
    def test_forget_single_item(self, memory: LongTermMemory) -> None:
        mem_id = memory.store("delete me")
        assert memory.count == 1
        memory.forget(mem_id)
        assert memory.count == 0
        with pytest.raises(MemoryNotFoundError):
            memory.retrieve(mem_id)

    def test_forget_nonexistent_is_noop(self, memory: LongTermMemory) -> None:
        memory.forget("ghost")
        assert memory.count == 0

    def test_forget_by_age(self, memory: LongTermMemory) -> None:
        memory.store("fresh", importance=0.5)
        old_id = memory.store("stale", importance=0.1)
        memory._store[old_id].created_at = time.time() - 100
        deleted = memory.forget_by_age(50)
        assert deleted == 1
        assert memory.count == 1
        assert memory.retrieve(next(iter(memory._store))).content == "fresh"


class TestMemoryMerge:
    def test_merge_two_related_memories(self, memory: LongTermMemory) -> None:
        id_a = memory.store("python basics", keywords=["python"], importance=0.6)
        id_b = memory.store("python advanced", keywords=["python"], importance=0.8)
        merged = memory.merge(id_a, id_b)
        assert merged.merged
        assert "python basics" in merged.content
        assert "python advanced" in merged.content
        assert merged.importance == 0.8
        assert "python" in merged.keywords

    def test_merge_removes_originals(self, memory: LongTermMemory) -> None:
        id_a = memory.store("a", keywords=["x"], importance=0.3)
        id_b = memory.store("b", keywords=["y"], importance=0.7)
        memory.merge(id_a, id_b)
        with pytest.raises(MemoryNotFoundError):
            memory.retrieve(id_a)
        with pytest.raises(MemoryNotFoundError):
            memory.retrieve(id_b)

    def test_merge_deduplicates_keywords(self, memory: LongTermMemory) -> None:
        id_a = memory.store("dup", keywords=["shared", "a"], importance=0.5)
        id_b = memory.store("dup too", keywords=["shared", "b"], importance=0.6)
        merged = memory.merge(id_a, id_b)
        assert set(merged.keywords) == {"shared", "a", "b"}


class TestMemoryImportance:
    def test_high_importance_returns_first(self, memory: LongTermMemory) -> None:
        memory.store("low", importance=0.1)
        memory.store("high", importance=0.9)
        memory.store("mid", importance=0.5)
        top = memory.list_by_importance(limit=2)
        assert top[0].content == "high"
        assert top[1].content == "mid"

    def test_importance_limit_respected(self, memory: LongTermMemory) -> None:
        for i in range(5):
            memory.store(f"item_{i}", importance=i * 0.2)
        top = memory.list_by_importance(limit=3)
        assert len(top) == 3


class TestMemoryCapacity:
    def test_exceeds_max_evicts_least_important(self, memory: LongTermMemory) -> None:
        for i in range(10):
            memory.store(f"keep_{i}", importance=0.5 + i * 0.05)
        memory.store("evicted", importance=0.01)
        assert memory.count == 10
        remaining = [m.content for m in memory._store.values()]
        assert "evicted" not in remaining

    def test_all_high_importance_preserved(self, memory: LongTermMemory) -> None:
        for i in range(9):
            memory.store(f"high_{i}", importance=0.9)
        memory.store("new_low", importance=0.01)
        assert memory.count == 10

    def test_custom_max_items(self) -> None:
        m = LongTermMemory(max_items=3)
        m.store("a", importance=0.1)
        m.store("b", importance=0.2)
        m.store("c", importance=0.3)
        m.store("d", importance=0.4)
        assert m.count == 3


class TestEmptyMemory:
    def test_search_keyword_returns_empty(self, memory: LongTermMemory) -> None:
        assert memory.search_by_keyword("anything") == []

    def test_search_semantic_returns_empty(self, memory: LongTermMemory) -> None:
        assert memory.search_semantic("anything") == []

    def test_list_by_importance_returns_empty(self, memory: LongTermMemory) -> None:
        assert memory.list_by_importance() == []

    def test_forget_by_age_returns_zero(self, memory: LongTermMemory) -> None:
        assert memory.forget_by_age(999) == 0
