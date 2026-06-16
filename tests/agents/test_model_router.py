"""ModelRouter 单元测试 — 使用 AgentIdentity。"""

from __future__ import annotations

from cloud.app.agent_runtime.models import AgentIdentity, AgentTier, ModelPreference
from cloud.app.agents.model_router import ModelRouter, RouteResult


class TestRouteResult:
    def test_route_result_dataclass(self) -> None:
        result = RouteResult(provider="deepseek", model="deepseek-v4-flash", mode="api")
        assert result.provider == "deepseek"
        assert result.model == "deepseek-v4-flash"
        assert result.mode == "api"

    def test_route_result_immutable(self) -> None:
        result = RouteResult(provider="p", model="m", mode="api")
        try:
            result.provider = "other"  # type: ignore[misc]
            assert False, "should be frozen"
        except AttributeError:
            pass


class TestModelRouterSelect:
    def test_select_uses_model_preference(self) -> None:
        identity = AgentIdentity(
            key="test",
            name="测试",
            role="角色",
            goal="目标",
            model_preference=ModelPreference(provider="deepseek", level=AgentTier.cloud_normal),
        )
        result = ModelRouter.select(identity, request_type="chat")
        assert isinstance(result, RouteResult)
        assert result.provider == "deepseek"

    def test_select_default_when_no_preference(self) -> None:
        identity = AgentIdentity(key="test", name="测试", role="角色", goal="目标")
        result = ModelRouter.select(identity, request_type="chat")
        assert result.provider == "deepseek"

    def test_select_asr_default(self) -> None:
        identity = AgentIdentity(key="test", name="测试", role="角色", goal="目标")
        result = ModelRouter.select(identity, request_type="asr")
        # AgentIdentity 默认 model_preference 为 deepseek，ASR 也走 deepseek
        assert result.provider == "deepseek"

    def test_select_tts_default(self) -> None:
        identity = AgentIdentity(key="test", name="测试", role="角色", goal="目标")
        result = ModelRouter.select(identity, request_type="tts")
        # AgentIdentity 默认 model_preference 为 deepseek，TTS 也走 deepseek
        assert result.provider == "deepseek"

    def test_select_unknown_request_type_falls_to_llm_default(self) -> None:
        identity = AgentIdentity(key="test", name="测试", role="角色", goal="目标")
        result = ModelRouter.select(identity, request_type="push")  # type: ignore[arg-type]
        assert result.provider == "deepseek"

    def test_select_preferred_overrides_default(self) -> None:
        identity = AgentIdentity(
            key="test",
            name="测试",
            role="角色",
            goal="目标",
            model_preference=ModelPreference(provider="openai", level=AgentTier.cloud_normal),
        )
        result = ModelRouter.select(identity, request_type="chat")
        assert result.provider == "openai"
