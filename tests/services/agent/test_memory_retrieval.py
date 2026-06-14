"""记忆检索策略测试。"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import pytest


@dataclass
class MemoryRecord:
    id: str
    content: str
    keywords: list[str] = field(default_factory=list)
    importance: float = 0.0
    created_at: float = field(default_factory=time.time)

    def relevance(self, query: str) -> float:
        q = query.lower()
        score = 0.0
        if q in self.content.lower():
            score += 1.0
        for kw in self.keywords:
            if q in kw.lower():
                score += 0.8
                break
        for word in q.split():
            if word in self.content.lower():
                score += 0.5
        return round(score, 4)


class MemoryStore:
    def __init__(self) -> None:
        self._records: dict[str, MemoryRecord] = {}

    def add(self, content: str, keywords: list[str] | None = None, importance: float = 0.0) -> MemoryRecord:
        mid = f"rec_{len(self._records) + 1}"
        rec = MemoryRecord(id=mid, content=content, keywords=keywords or [], importance=importance)
        self._records[mid] = rec
        return rec

    def _add_with_time(
        self, content: str, keywords: list[str] | None = None, importance: float = 0.0, created_at: float | None = None
    ) -> MemoryRecord:
        mid = f"rec_{len(self._records) + 1}"
        rec = MemoryRecord(id=mid, content=content, keywords=keywords or [], importance=importance, created_at=created_at or time.time())
        self._records[mid] = rec
        return rec

    def keyword_search(self, token: str) -> list[MemoryRecord]:
        results = []
        for rec in self._records.values():
            if any(token.lower() in kw.lower() for kw in rec.keywords):
                results.append(rec)
        return results

    def time_range_search(self, start_time: float, end_time: float) -> list[MemoryRecord]:
        return [rec for rec in self._records.values() if start_time <= rec.created_at <= end_time]

    def combined_search(
        self, keyword: str | None = None, start_time: float | None = None, end_time: float | None = None, min_importance: float | None = None
    ) -> list[MemoryRecord]:
        results = list(self._records.values())
        if keyword:
            results = [r for r in results if any(keyword.lower() in kw.lower() for kw in r.keywords)]
        if start_time is not None:
            results = [r for r in results if r.created_at >= start_time]
        if end_time is not None:
            results = [r for r in results if r.created_at <= end_time]
        if min_importance is not None:
            results = [r for r in results if r.importance >= min_importance]
        return results

    def sort_by_relevance(self, query: str, records: list[MemoryRecord] | None = None) -> list[MemoryRecord]:
        targets = records if records is not None else list(self._records.values())
        return sorted(targets, key=lambda r: r.relevance(query), reverse=True)

    def sort_by_time(self, records: list[MemoryRecord] | None = None, reverse: bool = True) -> list[MemoryRecord]:
        targets = records if records is not None else list(self._records.values())
        return sorted(targets, key=lambda r: r.created_at, reverse=reverse)

    def sort_by_importance(self, records: list[MemoryRecord] | None = None, reverse: bool = True) -> list[MemoryRecord]:
        targets = records if records is not None else list(self._records.values())
        return sorted(targets, key=lambda r: r.importance, reverse=reverse)

    def fuzzy_search(self, partial: str) -> list[tuple[MemoryRecord, float]]:
        p = partial.lower()
        scored = []
        for rec in self._records.values():
            match_count = 0
            for word in p.split():
                if word in rec.content.lower():
                    match_count += 1
                if any(word in kw.lower() for kw in rec.keywords):
                    match_count += 1
            if match_count > 0:
                score = round(match_count / max(len(p.split()), 1), 4)
                scored.append((rec, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    @property
    def count(self) -> int:
        return len(self._records)

    def clear(self) -> None:
        self._records.clear()


@pytest.fixture
def store() -> MemoryStore:
    s = MemoryStore()
    s.add("machine learning basics", keywords=["ml", "ai"], importance=0.9)
    s.add("python programming guide", keywords=["python", "coding"], importance=0.7)
    s.add("data science workflow", keywords=["data", "ml"], importance=0.8)
    s.add("web development react", keywords=["react", "frontend"], importance=0.5)
    s.add("database design patterns", keywords=["sql", "db"], importance=0.6)
    return s


class TestKeywordSearch:
    def test_exact_token_match(self, store: MemoryStore) -> None:
        results = store.keyword_search("ml")
        assert len(results) == 2
        assert all("ml" in r.keywords for r in results)

    def test_case_insensitive_match(self, store: MemoryStore) -> None:
        results = store.keyword_search("ML")
        assert len(results) == 2

    def test_no_match_returns_empty(self, store: MemoryStore) -> None:
        results = store.keyword_search("nonexistent")
        assert results == []

    def test_partial_token_match(self, store: MemoryStore) -> None:
        store.add("advanced ML techniques", keywords=["machine-learning"], importance=0.4)
        results = store.keyword_search("machine")
        assert len(results) == 1
        assert results[0].keywords == ["machine-learning"]


class TestTimeRangeSearch:
    def test_time_range_returns_matching(self, store: MemoryStore) -> None:
        store.clear()
        now = time.time()
        store._add_with_time("recent", keywords=["new"], importance=0.3, created_at=now - 10)
        store._add_with_time("old", keywords=["old"], importance=0.1, created_at=now - 1000)
        results = store.time_range_search(now - 100, now)
        assert len(results) == 1
        assert results[0].content == "recent"

    def test_time_range_exact_boundary(self, store: MemoryStore) -> None:
        store.clear()
        now = time.time()
        store._add_with_time("boundary", keywords=["b"], importance=0.2, created_at=now)
        results = store.time_range_search(now - 1, now + 1)
        assert len(results) == 1

    def test_time_range_no_match(self, store: MemoryStore) -> None:
        results = store.time_range_search(0, 1)
        assert results == []


class TestCombinedSearch:
    def test_keyword_and_time_range(self, store: MemoryStore) -> None:
        store.clear()
        now = time.time()
        store._add_with_time("ai recent", keywords=["ml", "ai"], importance=0.9, created_at=now - 10)
        store._add_with_time("ai old", keywords=["ml", "ai"], importance=0.9, created_at=now - 1000)
        results = store.combined_search(keyword="ml", start_time=now - 100, end_time=now)
        assert len(results) == 1
        assert results[0].content == "ai recent"

    def test_keyword_and_importance(self, store: MemoryStore) -> None:
        store.add("low importance ml", keywords=["ml"], importance=0.2)
        results = store.combined_search(keyword="ml", min_importance=0.5)
        for r in results:
            assert r.importance >= 0.5

    def test_all_filters_combined(self, store: MemoryStore) -> None:
        store.clear()
        now = time.time()
        store._add_with_time("filtered", keywords=["ml"], importance=0.9, created_at=now - 10)
        store._add_with_time("too old", keywords=["ml"], importance=0.9, created_at=now - 1000)
        store._add_with_time("low importance", keywords=["ml"], importance=0.1, created_at=now - 10)
        results = store.combined_search(keyword="ml", start_time=now - 100, end_time=now, min_importance=0.5)
        assert len(results) == 1
        assert results[0].content == "filtered"

    def test_no_filters_returns_all(self, store: MemoryStore) -> None:
        results = store.combined_search()
        assert len(results) == store.count


class TestSearchSorting:
    def test_sort_by_relevance_desc(self, store: MemoryStore) -> None:
        store.add("machine learning advanced", keywords=["ml", "deep"], importance=0.95)
        results = store.sort_by_relevance("machine learning")
        assert results[0].relevance("machine learning") >= results[-1].relevance("machine learning")

    def test_sort_by_time_desc(self, store: MemoryStore) -> None:
        now = time.time()
        recs = [
            store._add_with_time("old", keywords=["a"], created_at=now - 100),
            store._add_with_time("new", keywords=["b"], created_at=now - 10),
            store._add_with_time("middle", keywords=["c"], created_at=now - 50),
        ]
        sorted_recs = store.sort_by_time(recs)
        assert sorted_recs[0].content == "new"
        assert sorted_recs[-1].content == "old"

    def test_sort_by_importance_desc(self, store: MemoryStore) -> None:
        results = store.sort_by_importance()
        for i in range(len(results) - 1):
            assert results[i].importance >= results[i + 1].importance


class TestEmptyResults:
    def test_keyword_search_empty(self) -> None:
        s = MemoryStore()
        assert s.keyword_search("anything") == []

    def test_time_range_search_empty(self) -> None:
        s = MemoryStore()
        assert s.time_range_search(0, 1) == []

    def test_combined_search_empty(self) -> None:
        s = MemoryStore()
        assert s.combined_search(keyword="ml") == []

    def test_sort_empty_returns_empty(self) -> None:
        s = MemoryStore()
        assert s.sort_by_relevance("query") == []
        assert s.sort_by_time() == []
        assert s.sort_by_importance() == []


class TestLargeScalePerformance:
    def test_retrieval_within_threshold(self) -> None:
        s = MemoryStore()
        for i in range(500):
            s.add(f"memory item number {i}", keywords=[f"tag_{i % 20}", "generic"], importance=i / 500)
        start = time.time()
        results = s.keyword_search("tag_5")
        elapsed = (time.time() - start) * 1000
        assert elapsed < 100
        assert len(results) > 0

    def test_combined_search_large_set(self) -> None:
        s = MemoryStore()
        for i in range(500):
            s.add(f"item {i}", keywords=["ml"], importance=i / 500)
        start = time.time()
        results = s.combined_search(keyword="ml", min_importance=0.5)
        elapsed = (time.time() - start) * 1000
        assert elapsed < 100
        assert len(results) > 0


class TestFuzzyMatch:
    def test_partial_keyword_match(self, store: MemoryStore) -> None:
        results = store.fuzzy_search("mac")
        matched = [r for r, s in results if "machine" in r.content.lower()]
        assert len(matched) > 0

    def test_fuzzy_returns_sorted_by_match_count(self, store: MemoryStore) -> None:
        store.add("machine learning and deep learning", keywords=["ml", "deep", "ai"], importance=0.99)
        results = store.fuzzy_search("machine learning")
        for i in range(len(results) - 1):
            assert results[i][1] >= results[i + 1][1]

    def test_fuzzy_no_match_returns_empty(self, store: MemoryStore) -> None:
        results = store.fuzzy_search("zzzzzxyz")
        assert results == []

    def test_fuzzy_returns_multi_word_matches(self, store: MemoryStore) -> None:
        store.add("python for data science", keywords=["python", "data"], importance=0.8)
        results = store.fuzzy_search("python data")
        assert len(results) >= 1
