"""Agent Registry tests."""

from cloud.app.agent_runtime.agent_registry import AgentRegistry


class TestAgentRegistry:
    def test_load_agents(self):
        """test load agents."""
        AgentRegistry._loaded = False
        AgentRegistry.load("agents")
        assert len(AgentRegistry._agents) > 0
        assert "compliance_monitor" in AgentRegistry._agents

    def test_get_existing_agent(self):
        """test get existing agent."""
        agent = AgentRegistry.get("compliance_monitor")
        assert agent is not None
        assert agent.identity.key == "compliance_monitor"
        assert agent.identity.name == "合规审查"

    def test_get_nonexistent_agent(self):
        """test get nonexistent agent."""
        agent = AgentRegistry.get("nonexistent_agent")
        assert agent is None
