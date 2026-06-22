"""Tests for CircuitBreaker."""

from cloud.app.agent_runtime.lifecycle.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
)


def test_normal_operation():
    """test normal operation."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
    result = cb.call(lambda: "ok")
    assert result == "ok"
    assert cb.state == CircuitState.CLOSED


def test_trips_after_threshold():
    """test trips after threshold."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

    def fail():
        """fail."""
        raise ValueError("fail")

    for _ in range(3):
        try:
            cb.call(fail)
        except ValueError:
            pass
    assert cb.state == CircuitState.OPEN


def test_half_open_recovers():
    """test half open recovers after recovery_timeout."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

    def fail():
        """fail."""
        raise ValueError("fail")

    for _ in range(2):
        try:
            cb.call(fail)
        except ValueError:
            pass
    assert cb.state == CircuitState.OPEN, "should be open after 2 failures"

    # wait for recovery_timeout to elapse
    import time

    time.sleep(0.15)

    result = cb.call(lambda: "recovered")
    assert result == "recovered"
    assert cb.state == CircuitState.CLOSED, "should reset to closed on success"


def test_half_open_fails_again():
    """test half open fails again - stays open."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

    def fail():
        """fail."""
        raise ValueError("fail")

    for _ in range(2):
        try:
            cb.call(fail)
        except ValueError:
            pass
    assert cb.state == CircuitState.OPEN, "should be open after 2 failures"

    # wait for recovery_timeout to elapse → transitions to HALF_OPEN
    import time

    time.sleep(0.15)

    # call fails again while in HALF_OPEN
    try:
        cb.call(fail)
    except ValueError:
        pass
    assert cb.state == CircuitState.OPEN, "should stay open after half_open failure"


def test_open_raises():
    """test open raises."""
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=60)

    def fail():
        """fail."""
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
    """test dict failure detection."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=60)
    result = cb.call(lambda: {"success": False, "error": "fail"})
    assert result["success"] is False
    result = cb.call(lambda: {"success": False, "error": "fail2"})
    assert cb.state == CircuitState.OPEN


def test_circuit_breaker_half_open():
    """test half open state transition after recovery_timeout."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

    def fail():
        """fail."""
        raise ValueError("fail")

    for _ in range(2):
        try:
            cb.call(fail)
        except ValueError:
            pass
    assert cb.state == CircuitState.OPEN, "should be open after 2 failures"

    # wait for recovery_timeout to elapse → auto-transitions to HALF_OPEN on next call
    import time

    time.sleep(0.15)

    # call at t > recovery_timeout → should transition to HALF_OPEN then fail
    try:
        cb.call(fail)
    except ValueError:
        pass
    assert cb.state == CircuitState.OPEN, "should go back to OPEN after half_open failure"


def test_circuit_breaker_reset():
    """test reset restores to CLOSED with zero failure count."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=60)

    def fail():
        """fail."""
        raise ValueError("fail")

    for _ in range(2):
        try:
            cb.call(fail)
        except ValueError:
            pass
    assert cb.state == CircuitState.OPEN

    cb.reset()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    assert cb.last_failure_time == 0.0

    result = cb.call(lambda: "ok after reset")
    assert result == "ok after reset"
    assert cb.state == CircuitState.CLOSED


def test_circuit_breaker_consecutive_failures():
    """test consecutive failures trigger circuit break at threshold."""
    cb = CircuitBreaker(failure_threshold=4, recovery_timeout=60)

    def fail():
        """fail."""
        raise ValueError("fail")

    for i in range(4):
        try:
            cb.call(fail)
        except ValueError:
            pass
        if i < 3:
            assert cb.state == CircuitState.CLOSED, f"failed at call {i + 1}"
        else:
            assert cb.state == CircuitState.OPEN, "should be open after 4th failure"
