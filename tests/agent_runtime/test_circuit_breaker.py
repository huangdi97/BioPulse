import pytest

from cloud.app.agent_runtime.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState


def test_initial_state():
    cb = CircuitBreaker()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_on_failure_triggers_open():
    cb = CircuitBreaker(failure_threshold=2)
    cb.on_failure()
    assert cb.state == CircuitState.CLOSED
    cb.on_failure()
    assert cb.state == CircuitState.OPEN


def test_on_success_resets():
    cb = CircuitBreaker(failure_threshold=1)
    cb.on_failure()
    assert cb.state == CircuitState.OPEN
    cb.on_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_call_success():
    cb = CircuitBreaker()
    result = cb.call(lambda: {"success": True, "data": "ok"})
    assert result["data"] == "ok"
    assert cb.state == CircuitState.CLOSED


def test_call_failure():
    cb = CircuitBreaker(failure_threshold=1)
    result = cb.call(lambda: {"success": False, "error": "fail"})
    assert result["error"] == "fail"
    assert cb.state == CircuitState.OPEN


def test_call_raises_on_open():
    cb = CircuitBreaker(failure_threshold=1)
    cb.on_failure()
    with pytest.raises(CircuitBreakerOpenError):
        cb.call(lambda: {"success": True})


def test_reset():
    cb = CircuitBreaker(failure_threshold=1)
    cb.on_failure()
    assert cb.state == CircuitState.OPEN
    cb.reset()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
