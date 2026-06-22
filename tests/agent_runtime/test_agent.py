"""Tests for agent module — validates module imports correctly."""

from cloud.app.agent_runtime.core.agent import Agent


def test_agent_imports():
    """Agent class can be imported and is not None."""
    assert Agent is not None
