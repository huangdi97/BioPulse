"""Tests for CircuitBreaker."""

from unittest.mock import patch

from cloud.app.agent_runtime.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
)


def test_normal_operation():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
    result = cb.call(lambda: "ok")
    assert result == "ok"
    assert cb.state == CircuitState.CLOSED


def test_trips_after_threshold():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

    def fail():
        raise ValueError("fail")

    for _ in range(3):
        try:
            cb.call(fail)
        except ValueError:
            pass
    assert cb.state == CircuitState.OPEN


def test_half_open_recovers():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

    def fail():
        raise ValueError("fail")

    with patch("cloud.app.agent_runtime.circuit_breaker.time.time", side_effect=[0, 0, 0, 0, 0, 1.1]):
        for _ in range(2):
            try:
                cb.call(fail)
            except ValueError:
                pass
        assert cb.state == CircuitState.OPEN
        result = cb.call(lambda: "recovered")
        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED


def test_half_open_fails_again():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

    def fail():
        raise ValueError("fail")

    with patch("cloud.app.agent_runtime.circuit_breaker.time.time", side_effect=[0, 0, 0, 0, 0, 1.1, 1.1, 1.1, 1.1, 1.1]):
        for _ in range(2):
            try:
                cb.call(fail)
            except ValueError:
                pass
        for _ in range(2):
            try:
                cb.call(fail)
            except (ValueError, CircuitBreakerOpenError):
                pass
        assert cb.state == CircuitState.OPEN


def test_open_raises():
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=60)

    def fail():
        raise ValueError("fail")

    try:
        cb.call(fail)
    except ValueError:
        pass
    try:
        cb.call(lambda: "should not reach")
        assert False, "Expected CircuitBreakerOpenError"
    except CircuitBreakerOpenError:
        pass


def test_dict_failure_detection():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=60)
    result = cb.call(lambda: {"success": False, "error": "fail"})
    assert result["success"] is False
    result = cb.call(lambda: {"success": False, "error": "fail2"})
    assert cb.state == CircuitState.OPEN
