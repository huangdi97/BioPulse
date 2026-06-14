"""ToolBridge 安全测试 — caller_agent_id 白名单过滤。"""

from __future__ import annotations

from cloud.app.agent_runtime.models import ToolDef
from cloud.app.agent_runtime.tool_bridge import ToolBridge, ToolResult


class TestToolBridgeExecuteAllowedAgents:
    def test_empty_allowed_agents_allows_any(self) -> None:
        bridge = ToolBridge()
        bridge.register_tool(ToolDef(name="test_tool", description="test", params={}))
        result = bridge.execute("test_tool", caller_agent_id="any_agent")
        assert isinstance(result, ToolResult)
        assert result.success is True

    def test_allowed_agent_can_call(self) -> None:
        bridge = ToolBridge()
        bridge.register_tool(ToolDef(name="restricted_tool", description="restricted", params={}, allowed_agents=["agent_a", "agent_b"]))
        result = bridge.execute("restricted_tool", caller_agent_id="agent_a")
        assert result.success is True

    def test_disallowed_agent_gets_error(self) -> None:
        bridge = ToolBridge()
        bridge.register_tool(ToolDef(name="restricted_tool", description="restricted", params={}, allowed_agents=["agent_a"]))
        result = bridge.execute("restricted_tool", caller_agent_id="agent_c")
        assert result.success is False
        assert result.error == "agent not allowed"

    def test_unknown_tool_returns_error(self) -> None:
        bridge = ToolBridge()
        result = bridge.execute("nonexistent", caller_agent_id="agent_a")
        assert result.success is False
        assert "unknown tool" in result.error

    def test_execute_without_caller_agent_allows_any(self) -> None:
        bridge = ToolBridge()
        bridge.register_tool(ToolDef(name="restricted_tool", description="restricted", params={}, allowed_agents=["agent_a"]))
        result = bridge.execute("restricted_tool")
        assert result.success is True

    def test_multiple_allowed_agents(self) -> None:
        bridge = ToolBridge()
        bridge.register_tool(ToolDef(name="shared_tool", description="shared", params={}, allowed_agents=["agent_x", "agent_y", "agent_z"]))
        assert bridge.execute("shared_tool", caller_agent_id="agent_x").success is True
        assert bridge.execute("shared_tool", caller_agent_id="agent_y").success is True
        assert bridge.execute("shared_tool", caller_agent_id="agent_z").success is True
        assert bridge.execute("shared_tool", caller_agent_id="agent_w").success is False

    def test_default_tools_allow_all(self) -> None:
        bridge = ToolBridge()
        bridge.register_default_tools()
        for tool_name in bridge._tools:
            result = bridge.execute(tool_name, caller_agent_id="any_agent")
            assert result.success is True, f"tool {tool_name} should be accessible"
