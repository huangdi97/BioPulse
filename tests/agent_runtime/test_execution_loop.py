"""Tests for execution_loop module — validates module imports correctly."""

from cloud.app.agent_runtime.execution_loop import ExecutionEngine


def test_execution_engine_imports():
    """ExecutionEngine class can be imported and is not None."""
    assert ExecutionEngine is not None
