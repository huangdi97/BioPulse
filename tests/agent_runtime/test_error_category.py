"""Tests for runtime_core — error_category categorization."""

from cloud.app.agent_runtime.core.runtime_core import RuntimeCore


def test_categorize_error_timeout():
    assert RuntimeCore._categorize_error("timeout") == "timeout"


def test_categorize_error_llm_failed():
    assert RuntimeCore._categorize_error("llm_failed") == "llm_failed"


def test_categorize_error_budget_exceeded():
    assert RuntimeCore._categorize_error("budget_exceeded") == "budget_exceeded"


def test_categorize_error_rate_limited():
    assert RuntimeCore._categorize_error("rate_limited") == "rate_limited"


def test_categorize_error_blocked():
    assert RuntimeCore._categorize_error("blocked") == "validation_failed"


def test_categorize_error_unknown():
    assert RuntimeCore._categorize_error("foobar") == "unknown"


def test_categorize_error_success():
    assert RuntimeCore._categorize_error("success") == "unknown"


def test_categorize_error_bulkhead():
    assert RuntimeCore._categorize_error("bulkhead_rejected") == "rate_limited"


def test_categorize_error_degraded():
    assert RuntimeCore._categorize_error("degraded") == "tool_error"


def test_categorize_error_incomplete():
    assert RuntimeCore._categorize_error("incomplete") == "unknown"
