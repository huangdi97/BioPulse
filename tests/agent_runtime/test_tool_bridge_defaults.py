"""Tests for tool_bridge_defaults module."""

from cloud.app.agent_runtime.tool_bridge_defaults import BRAIN_TOOLS, DEFAULT_TOOLS


def test_default_tools_count():
    """DEFAULT_TOOLS should contain 25 tools."""
    assert len(DEFAULT_TOOLS) == 23


def test_brain_tools_count():
    """BRAIN_TOOLS should contain 2 tools."""
    assert len(BRAIN_TOOLS) == 2


def test_all_tools_have_name():
    """Every tool must have a name."""
    for t in DEFAULT_TOOLS + BRAIN_TOOLS:
        assert t.name, "Tool name should not be empty"


def test_unique_tool_names():
    """Tool names must be unique."""
    names = [t.name for t in DEFAULT_TOOLS + BRAIN_TOOLS]
    assert len(names) == len(set(names))


def test_query_bidding_allowed_agents():
    """query_bidding should be allowed for opportunity_scanner."""
    tools = {t.name: t for t in DEFAULT_TOOLS}
    assert "opportunity_scanner" in tools["query_bidding"].allowed_agents


def test_agent_brain_set_permission():
    """agent_brain_set should have write permission."""
    tools = {t.name: t for t in BRAIN_TOOLS}
    assert tools["agent_brain_set"].permission_level == "write"
