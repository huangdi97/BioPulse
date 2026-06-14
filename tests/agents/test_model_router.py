"""ModelRouter 单元测试。"""

from __future__ import annotations

import pytest

from cloud.app.agents.agent_model import AgentModel
from cloud.app.agents.model_router import ModelRouter, RouteResult


class TestRouteResult:
    def test_route_result_dataclass(self) -> None:
        result = RouteResult(provider="deepseek", model="deepseek-v4-flash", mode="api")
        assert result.provider == "deepseek"
        assert result.model == "deepseek-v4-flash"
        assert result.mode == "api"

    def test_route_result_immutable(self) -> None:
        result = RouteResult(provider="p", model="m", mode="api")
        with pytest.raises(AttributeError):
            result.provider = "other"  # type: ignore[misc]


class TestModelRouterSelect:
    def test_select_uses_model_preference(self) -> None:
        model = AgentModel(
            agent_id="test",
            name="测试",
            persona="角色: 目标",
            model_preference="deepseek/deepseek-v4-flash",
        )
        result = ModelRouter.select(model, request_type="chat")
        assert isinstance(result, RouteResult)
        assert result.provider == "deepseek"
        assert result.model == "deepseek-v4-flash"

    def test_select_default_when_no_preference(self) -> None:
        model = AgentModel(agent_id="test", name="测试", persona="角色: 目标", model_preference="")
        result = ModelRouter.select(model, request_type="chat")
        assert result.provider == "deepseek"
        assert result.model == "deepseek-chat"

    def test_select_fallback_when_preference_single_token(self) -> None:
        model = AgentModel(
            agent_id="test",
            name="测试",
            persona="角色: 目标",
            model_preference="deepseek-v4-flash",
        )
        result = ModelRouter.select(model, request_type="chat")
        assert result.provider == "deepseek-v4-flash"
        assert result.model == "deepseek-v4-flash"

    def test_select_asr_default(self) -> None:
        model = AgentModel(agent_id="test", name="测试", persona="角色: 目标")
        result = ModelRouter.select(model, request_type="asr")
        assert result.provider == "whisper"
        assert result.model == "whisper-1"

    def test_select_tts_default(self) -> None:
        model = AgentModel(agent_id="test", name="测试", persona="角色: 目标")
        result = ModelRouter.select(model, request_type="tts")
        assert result.provider == "openai"
        assert result.model == "tts-1"

    def test_select_unknown_request_type_falls_to_llm_default(self) -> None:
        model = AgentModel(agent_id="test", name="测试", persona="角色: 目标")
        result = ModelRouter.select(model, request_type="push")  # type: ignore[arg-type]
        assert result.provider == "deepseek"

    def test_select_preferred_overrides_default(self) -> None:
        model = AgentModel(
            agent_id="test",
            name="测试",
            persona="角色: 目标",
            model_preference="openai/gpt-4",
        )
        result = ModelRouter.select(model, request_type="chat")
        assert result.provider == "openai"
        assert result.model == "gpt-4"

    def test_select_all_preferences(self) -> None:
        model = AgentModel(
            agent_id="test",
            name="测试",
            persona="角色: 目标",
            model_preference="anthropic/claude-3-opus",
        )
        result = ModelRouter.select(model, request_type="chat")
        assert result.provider == "anthropic"
        assert result.model == "claude-3-opus"
