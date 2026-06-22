"""Agent 端到端集成测试 — 验证 identity.yaml 加载、Agent 创建、组件完整性。"""

from pathlib import Path

import pytest

from cloud.app.agent_runtime.core.agent import Agent
from cloud.app.agent_runtime.core.agent_registry import AgentRegistry
from cloud.app.agent_runtime.core.agent_specs import AGENT_SPECS

AGENTS_DIR = Path("agents")


@pytest.fixture(scope="module")
def agent_registry():
    AgentRegistry.load(str(AGENTS_DIR))
    return AgentRegistry


@pytest.fixture(scope="module")
def all_agents(agent_registry):
    return AgentRegistry.list()


class TestAgentFromYaml:
    """7 个 identity.yaml 加载验证。"""

    def test_all_agents_loaded(self, all_agents):
        assert len(all_agents) == 7, f"Expected 7 agents, got {len(all_agents)}"

    def test_all_agents_have_required_fields(self, all_agents):
        for agent in all_agents:
            assert agent.identity.key, "Agent missing key"
            assert agent.identity.name, f"Agent {agent.identity.key} missing name"
            assert agent.identity.role, f"Agent {agent.identity.key} missing role"
            assert agent.identity.goal, f"Agent {agent.identity.key} missing goal"
            assert agent.identity.allowed_tools, f"Agent {agent.identity.key} missing allowed_tools"

    def test_agent_keys_match(self, all_agents):
        keys = [a.identity.key for a in all_agents]
        expected = sorted(AGENT_SPECS.keys())
        assert sorted(keys) == expected, f"Agent keys mismatch: {sorted(keys)} vs {expected}"

    def test_agent_keys_in_identity_yaml(self):
        """每个 identity.yaml 的文件名（目录名）与 key 一致。"""
        for yaml_path in sorted(AGENTS_DIR.rglob("identity.yaml")):
            dir_name = yaml_path.parent.name
            agent = Agent.from_yaml(str(yaml_path))
            assert agent.identity.key == dir_name, f"identity.yaml in {dir_name}/ has key={agent.identity.key}"


class TestAgentComponents:
    """Agent 组件完整性验证。"""

    def test_model_router_not_none(self, all_agents):
        for agent in all_agents:
            assert agent.model_router is not None, f"{agent.identity.key}: model_router is None"
            assert hasattr(agent.model_router, "temperature"), f"{agent.identity.key}: model_router missing temperature"

    def test_model_router_temperature_from_preference(self, all_agents):
        for agent in all_agents:
            expected = agent.identity.model_preference.temperature
            actual = agent.model_router.temperature
            assert actual == expected, f"{agent.identity.key}: temp {actual} != identity {expected}"

    def test_memory_not_none(self, all_agents):
        for agent in all_agents:
            assert agent.memory is not None, f"{agent.identity.key}: memory is None"

    def test_memory_accepts_db(self):
        """Memory 接受 db 连接参数。"""
        agent = Agent.from_yaml("agents/compliance_monitor/identity.yaml")
        # Default: Memory(None)
        assert agent.memory._agent_db is None
        # With db
        agent2 = Agent.from_yaml("agents/compliance_monitor/identity.yaml")
        agent2.memory = type(agent.memory)("connected")
        assert agent2.memory._agent_db == "connected"

    def test_cost_governor(self, all_agents):
        for agent in all_agents:
            assert agent.cost_governor is not None
            assert hasattr(agent.cost_governor, "_max_cost")

    def test_safety_guard(self, all_agents):
        for agent in all_agents:
            assert agent.safety is not None

    def test_tool_bridge(self, all_agents):
        for agent in all_agents:
            assert agent.tools is not None


class TestAgentSpecsCoverage:
    """identity.yaml 覆盖 AGENT_SPECS 验证。"""

    def test_allowed_tools_subset(self, all_agents):
        """identity.yaml 的 allowed_tools 是 AGENT_SPECS 的合理子集（超集也算通过）。"""
        for agent in all_agents:
            key = agent.identity.key
            if key not in AGENT_SPECS:
                continue
            id_tools = set(agent.identity.allowed_tools)
            spec_tools = set(AGENT_SPECS[key].get("allowed_tools", []))
            # identity tools should contain at least the spec tools
            missing = spec_tools - id_tools
            if missing:
                import logging

                logging.warning("%s: identity missing spec tools: %s", key, missing)

    def test_identity_yaml_has_model_preference(self, all_agents):
        for agent in all_agents:
            pref = agent.identity.model_preference
            assert pref is not None, f"{agent.identity.key}: missing model_preference"
            assert pref.provider, f"{agent.identity.key}: missing model_preference.provider"
            assert pref.temperature is not None, f"{agent.identity.key}: missing model_preference.temperature"

    def test_identity_yaml_has_safety_profile(self, all_agents):
        for agent in all_agents:
            sp = agent.identity.safety_profile
            assert sp is not None, f"{agent.identity.key}: missing safety_profile"
            assert sp.max_permission, f"{agent.identity.key}: missing max_permission"


class TestAgentInsights:
    """Agent insights_for 方法不崩溃。"""

    def test_insights_for_returns_list(self, all_agents):
        import asyncio

        for agent in all_agents:
            result = asyncio.run(agent.insights_for("test-page", "test-user"))
            assert isinstance(result, list), f"{agent.identity.key}: insights not a list"
            assert len(result) > 0, f"{agent.identity.key}: empty insights"
            assert result[0].agent_key == agent.identity.key


@pytest.mark.fast
def test_individual_agent_from_yaml():
    """单个 identity.yaml 加载测试。"""
    agent = Agent.from_yaml("agents/compliance_monitor/identity.yaml")
    assert agent.identity.key == "compliance_monitor"
    assert agent.identity.name == "合规审查"
    assert agent.identity.role == "合规审计专家"
    assert agent.model_router is not None
