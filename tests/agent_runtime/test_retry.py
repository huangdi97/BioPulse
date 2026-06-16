"""Tests for retry module."""

from cloud.app.agent_runtime.retry import retry_with_backoff


def test_retry_success_first_try():
    result = retry_with_backoff(lambda: "ok", max_attempts=3)
    assert result["success"] is True
    assert result["data"] == "ok"
    assert result["attempts"] == 1


def test_retry_success_after_retry():
    counter = [0]

    def fn():
        counter[0] += 1
        if counter[0] < 2:
            raise TimeoutError("timeout")
        return "ok"

    result = retry_with_backoff(fn, max_attempts=3, base_delay=0.01)
    assert result["success"] is True
    assert result["data"] == "ok"
    assert result["attempts"] == 2


def test_retry_non_retryable_exception():
    result = retry_with_backoff(lambda: 1 / 0, max_attempts=3)
    assert result["success"] is False
    assert result["attempts"] == 1
    assert "division by zero" in result["error"]


def test_retry_exhaustion():
    attempts = [0]

    def fn():
        attempts[0] += 1
        raise TimeoutError("always fail")

    result = retry_with_backoff(fn, max_attempts=3, base_delay=0.01)
    assert result["success"] is False
    assert result["attempts"] == 3
