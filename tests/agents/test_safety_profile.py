"""SafetyProfile + AgentModel safety_profile 字段单元测试。"""

from __future__ import annotations

from unittest.mock import mock_open, patch

from cloud.app.agents.agent_model import AgentModel
from cloud.app.agents.agent_repository import AgentRepository
from cloud.app.agents.safety_profile import SafetyProfile


class TestSafetyProfile:
    def test_default_profile(self) -> None:
        profile = SafetyProfile()
        assert profile.allowed_tools == []
        assert profile.blocked_topics == []
        assert profile.max_turns_per_session == 50
        assert profile.requires_human_review is False

    def test_from_safety_level_read(self) -> None:
        profile = SafetyProfile.from_safety_level("read", allowed_tools=["tool_a"])
        assert profile.allowed_tools == ["tool_a"]
        assert "write" in profile.blocked_topics
        assert profile.max_turns_per_session == 100
        assert profile.requires_human_review is False

    def test_from_safety_level_write(self) -> None:
        profile = SafetyProfile.from_safety_level("write", allowed_tools=["tool_b"])
        assert profile.allowed_tools == ["tool_b"]
        assert profile.requires_human_review is True
        assert profile.max_turns_per_session == 50

    def test_from_safety_level_admin(self) -> None:
        profile = SafetyProfile.from_safety_level("admin")
        assert profile.blocked_topics == []
        assert profile.requires_human_review is False
        assert profile.max_turns_per_session == 200

    def test_from_safety_level_unknown(self) -> None:
        profile = SafetyProfile.from_safety_level("unknown")
        assert profile.allowed_tools == []
        assert profile.requires_human_review is False

    def test_check_topic_blocked(self) -> None:
        profile = SafetyProfile(blocked_topics=["delete", "admin"])
        assert profile.check_topic("please delete this record") == "delete"
        assert profile.check_topic("admin access required") == "admin"

    def test_check_topic_not_blocked(self) -> None:
        profile = SafetyProfile(blocked_topics=["delete", "admin"])
        assert profile.check_topic("hello world") is None

    def test_llm_audit_placeholder_always_passes(self) -> None:
        profile = SafetyProfile()
        assert profile.llm_audit_placeholder("any message") is True


SAMPLE_YAML_WITH_SAFETY = {
    "key": "test_agent",
    "name": "测试",
    "role": "测试角色",
    "goal": "测试目标",
    "allowed_tools": ["tool_a", "tool_b"],
    "model_preference": {"provider": "deepseek", "level": "cloud_normal", "temperature": 0.3},
    "trigger_mode": "user_request",
    "safety_profile": {
        "max_permission": "write",
        "bulkhead_max_concurrent": 2,
        "rate_limit_per_minute": 10,
    },
}


class TestAgentModelSafetyProfile:
    def test_agent_model_has_safety_profile(self) -> None:
        model = AgentModel(agent_id="test", name="测试", persona="角色: 目标")
        assert hasattr(model, "safety_profile")
        assert isinstance(model.safety_profile, SafetyProfile)

    def test_safety_profile_from_yaml_write(self) -> None:
        with patch("cloud.app.agents.agent_repository.yaml.safe_load", return_value=SAMPLE_YAML_WITH_SAFETY):
            with patch("cloud.app.agents.agent_repository.open", new_callable=mock_open):
                model = AgentRepository.load("test_agent", agents_dir="/fake/agents")
                assert model is not None
                assert model.safety_level == "write"
                assert model.safety_profile.allowed_tools == ["tool_a", "tool_b"]
                assert model.safety_profile.requires_human_review is True

    def test_safety_profile_from_yaml_read(self) -> None:
        yaml_data = dict(SAMPLE_YAML_WITH_SAFETY)
        yaml_data["safety_profile"] = {"max_permission": "read"}
        with patch("cloud.app.agents.agent_repository.yaml.safe_load", return_value=yaml_data):
            with patch("cloud.app.agents.agent_repository.open", new_callable=mock_open):
                model = AgentRepository.load("test_agent", agents_dir="/fake/agents")
                assert model is not None
                assert model.safety_level == "read"
                assert model.safety_profile.requires_human_review is False

    def test_specialized_agent_blocks_topic(self) -> None:
        from cloud.app.agents.base_agent import AgentContext
        from cloud.app.agents.specialized_agent import SpecializedAgent

        model = AgentModel(
            agent_id="blocked_test",
            name="拦截测试",
            persona="测试: 拦截",
            safety_level="read",
            safety_profile=SafetyProfile.from_safety_level("read"),
        )
        agent = SpecializedAgent.from_model(model)
        import asyncio

        response = asyncio.run(agent.execute(AgentContext(message="帮我写入数据")))
        assert "安全拦截" in response.reply

    def test_specialized_agent_allows_safe_topic(self) -> None:
        from cloud.app.agents.base_agent import AgentContext
        from cloud.app.agents.specialized_agent import SpecializedAgent

        model = AgentModel(
            agent_id="safe_test",
            name="安全测试",
            persona="测试: 安全",
            safety_level="read",
            safety_profile=SafetyProfile.from_safety_level("read"),
        )
        agent = SpecializedAgent.from_model(model)
        import asyncio

        response = asyncio.run(agent.execute(AgentContext(message="查询数据")))
        assert "安全拦截" not in response.reply
