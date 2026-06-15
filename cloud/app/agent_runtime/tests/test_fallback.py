"""Tests for LLM fallback chain."""

from cloud.app.agent_runtime.runtime_llm import AllModelsFailedError, get_fallback_chain


def test_fallback_chain_has_expected_providers():
    providers = [p["provider"] for p in get_fallback_chain()]
    assert "deepseek" in providers
    assert "openrouter" in providers
    assert "openai" in providers


def test_all_models_failed_error():
    errors = [
        {"provider": "deepseek", "model": "deepseek-v4-flash", "error": "timeout", "elapsed": 5.0},
        {"provider": "openai", "model": "gpt-4o-mini", "error": "auth failed", "elapsed": 2.0},
    ]
    exc = AllModelsFailedError(errors)
    assert "2 errors" in str(exc)
    assert exc.errors == errors


def test_call_provider_missing_key():
    from cloud.app.agent_runtime.runtime_llm import RuntimeLLM

    provider = {"provider": "test", "model": "test-model", "env_key": "NONEXISTENT_KEY_12345", "url": "http://localhost:0/test"}
    result = RuntimeLLM._call_provider([{"role": "user", "content": "hello"}], 0.5, provider)
    assert result["success"] is False
    assert "No API key" in result["error"]
