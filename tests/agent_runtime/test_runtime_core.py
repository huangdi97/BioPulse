"""Tests for runtime_core module — validates module imports correctly."""

from cloud.app.agent_runtime.core.runtime_core import RuntimeCore


def test_runtime_core_imports():
    """RuntimeCore class can be imported and is not None."""
    assert RuntimeCore is not None
