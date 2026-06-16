from cloud.app.agent_runtime.models import ToolDef


def test_tool_def_defaults():
    tool = ToolDef(name="test", description="desc", params={})
    assert tool.permission_level == "read"
    assert tool.allowed_agents == []


def test_tool_def_custom():
    tool = ToolDef(name="admin_tool", description="admin", params={}, permission_level="admin", allowed_agents=["agent1"])
    assert tool.permission_level == "admin"
    assert tool.allowed_agents == ["agent1"]
