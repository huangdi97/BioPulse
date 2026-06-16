"""Tests for safety_guard module — validates module imports correctly."""

from cloud.app.agent_runtime.safety_guard import SafetyGuard


def test_safety_guard_init():
    """SafetyGuard can be instantiated with default arguments."""
    guard = SafetyGuard()
    assert guard is not None
