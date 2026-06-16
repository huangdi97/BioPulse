"""Tests for runtime_llm/core module."""

from cloud.app.agent_runtime.runtime_llm.core import RuntimeLLM


def test_runtime_llm_imports():
    """RuntimeLLM class can be imported."""
    assert RuntimeLLM is not None


def test_runtime_llm_has_methods():
    """RuntimeLLM should have expected public methods."""
    methods = [m for m in dir(RuntimeLLM) if not m.startswith("_")]
    assert "call_llm_with_fallback" in methods
