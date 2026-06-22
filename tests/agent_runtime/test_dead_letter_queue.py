"""Tests for dead_letter_queue — replay_all, replay_by_error_type, get_stats."""

from cloud.app.agent_runtime.lifecycle.dead_letter_queue import DeadLetterEntry, DeadLetterQueue


def test_dead_letter_entry_with_error_category():
    entry = DeadLetterEntry("test_agent", "input", "error", error_category="timeout")
    d = entry.to_dict()
    assert d["error_category"] == "timeout"
    restored = DeadLetterEntry.from_dict(d)
    assert restored.error_category == "timeout"


def test_dead_letter_entry_default_category():
    entry = DeadLetterEntry("test_agent", "input", "error")
    assert entry.error_category == "unknown"


def test_replay_all():
    dlq = DeadLetterQueue()
    dlq.push(DeadLetterEntry("a1", "in1", "err1", error_category="timeout"))
    dlq.push(DeadLetterEntry("a2", "in2", "err2", error_category="llm_failed"))
    dlq.push(DeadLetterEntry("a3", "in3", "err3", error_category="timeout"))
    results = dlq.replay_all(max_retries=3)
    assert len(results) == 3
    assert all(r["retried"] for r in results)
    assert dlq.get_stats()["total"] == 3


def test_replay_by_error_type():
    dlq = DeadLetterQueue()
    dlq.push(DeadLetterEntry("a1", "in1", "err1", error_category="timeout"))
    dlq.push(DeadLetterEntry("a2", "in2", "err2", error_category="llm_failed"))
    dlq.push(DeadLetterEntry("a3", "in3", "err3", error_category="timeout"))
    results = dlq.replay_by_error_type("timeout", max_retries=5)
    assert len(results) == 2
    assert all(r["error_category"] == "timeout" for r in results)


def test_replay_by_error_type_none_match():
    dlq = DeadLetterQueue()
    dlq.push(DeadLetterEntry("a1", "in1", "err1", error_category="timeout"))
    results = dlq.replay_by_error_type("budget_exceeded")
    assert len(results) == 0


def test_get_stats():
    dlq = DeadLetterQueue()
    dlq.push(DeadLetterEntry("a1", "in1", "err1", error_category="timeout"))
    dlq.push(DeadLetterEntry("a2", "in2", "err2", error_category="llm_failed"))
    dlq.push(DeadLetterEntry("a3", "in3", "err3", error_category="timeout"))
    stats = dlq.get_stats()
    assert stats["total"] == 3
    assert stats["by_error_type"]["timeout"] == 2
    assert stats["by_error_type"]["llm_failed"] == 1


def test_retry_exhausted():
    dlq = DeadLetterQueue()
    entry = DeadLetterEntry("a1", "in1", "err1", retry_count=3, error_category="timeout")
    dlq.push(entry)
    results = dlq.replay_all(max_retries=3)
    assert results[0]["retried"] is False


def test_empty_dlq():
    dlq = DeadLetterQueue()
    assert dlq.replay_all() == []
    assert dlq.replay_by_error_type("timeout") == []
    assert dlq.get_stats() == {"total": 0, "by_error_type": {}}
