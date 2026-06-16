"""AgentIdentity + agent_runtime SafetyProfile 字段单元测试。"""

from __future__ import annotations

from unittest.mock import mock_open, patch

from cloud.app.agent_runtime.models import (
    AgentIdentity,
    ModelPreference,
    SafetyProfile,
)
from cloud.app.agents.agent_repository import AgentRepository


class TestSafetyProfile:
    def test_default_profile(self) -> None:
        profile = SafetyProfile()
        assert profile.max_permission == "read"
        assert profile.bulkhead_max_concurrent == 5
        assert profile.rate_limit_per_minute == 30

    def test_custom_profile(self) -> None:
        profile = SafetyProfile(
            max_permission="write",
            bulkhead_max_concurrent=2,
            rate_limit_per_minute=10,
        )
        assert profile.max_permission == "write"
        assert profile.bulkhead_max_concurrent == 2
        assert profile.rate_limit_per_minute == 10


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


class TestAgentIdentitySafety:
    def test_agent_identity_has_safety_profile(self) -> None:
        identity = AgentIdentity(key="test", name="测试", role="角色", goal="目标")
        assert hasattr(identity, "safety_profile")
        assert isinstance(identity.safety_profile, SafetyProfile)

    def test_safety_profile_from_yaml_write(self) -> None:
        with patch("cloud.app.agents.agent_repository.yaml.safe_load", return_value=SAMPLE_YAML_WITH_SAFETY):
            with patch("cloud.app.agents.agent_repository.open", new_callable=mock_open):
                identity = AgentRepository.load("test_agent", agents_dir="/fake/agents")
                assert identity is not None
                assert identity.safety_profile.max_permission == "write"
                assert identity.safety_profile.bulkhead_max_concurrent == 2
                assert identity.safety_profile.rate_limit_per_minute == 10

    def test_safety_profile_from_yaml_read(self) -> None:
        yaml_data = dict(SAMPLE_YAML_WITH_SAFETY)
        yaml_data["safety_profile"] = {"max_permission": "read"}
        with patch("cloud.app.agents.agent_repository.yaml.safe_load", return_value=yaml_data):
            with patch("cloud.app.agents.agent_repository.open", new_callable=mock_open):
                identity = AgentRepository.load("test_agent", agents_dir="/fake/agents")
                assert identity is not None
                assert identity.safety_profile.max_permission == "read"

    def test_model_preference_parsed_correctly(self) -> None:
        with patch("cloud.app.agents.agent_repository.yaml.safe_load", return_value=SAMPLE_YAML_WITH_SAFETY):
            with patch("cloud.app.agents.agent_repository.open", new_callable=mock_open):
                identity = AgentRepository.load("test_agent", agents_dir="/fake/agents")
                assert identity is not None
                assert isinstance(identity.model_preference, ModelPreference)
                assert identity.model_preference.provider == "deepseek"
                assert identity.model_preference.level == "cloud_normal"
                assert identity.model_preference.temperature == 0.3
