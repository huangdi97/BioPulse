"""Tests for request module."""

from cloud.app.agent_runtime.runtime_llm.request import build_cloud_body


def test_build_cloud_body_basic():
    body = build_cloud_body(messages=[{"role": "user", "content": "hi"}], temperature=0.7)
    assert body["messages"] == [{"role": "user", "content": "hi"}]
    assert body["temperature"] == 0.7
    assert body["max_tokens"] == 2048
    assert "agent_mode" not in body


def test_build_cloud_body_agent_mode():
    body = build_cloud_body(messages=[], temperature=0.3, agent_mode=True)
    assert body["agent_mode"] is True
    assert body["temperature"] == 0.3


def test_call_provider_no_key():
    from cloud.app.agent_runtime.runtime_llm.request import call_provider

    result = call_provider(
        [{"role": "user", "content": "hi"}],
        0.7,
        {
            "provider": "test_prov",
            "model": "test",
            "env_key": "MISSING_KEY_THAT_DOES_NOT_EXIST_XYZ",
        },
    )
    assert result["success"] is False
    assert "No API key" in result["error"]
