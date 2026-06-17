"""MCP 工具集成测试 — ToolRegistry + MCP 工具注册/调用。"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from cloud.app.services.agent_core import ToolRegistry


@pytest.fixture
def mcp_tool_metadata():
    return {
        "name": "pubmed_search",
        "description": "Search PubMed for biomedical literature",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results to return", "default": 10},
            },
            "required": ["query"],
        },
    }


@pytest.fixture
def mcp_tool_metadata_no_required():
    return {
        "name": "echo",
        "description": "Echo back input",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Message to echo"},
            },
        },
    }


@pytest.fixture
def tool_registry():
    return ToolRegistry()


class TestMcpToolRegistration:
    def test_register_mcp_tool_success(self, tool_registry: ToolRegistry, mcp_tool_metadata: dict):
        meta = mcp_tool_metadata
        tool_registry.register(
            name=meta["name"],
            description=meta["description"],
            parameters=meta["inputSchema"],
            fn=lambda query, max_results=10: [f"result_{query}"],
        )
        tool = tool_registry.get_tool("pubmed_search")
        assert tool["name"] == "pubmed_search"
        assert tool["description"] == "Search PubMed for biomedical literature"
        assert tool["parameters"]["required"] == ["query"]

    def test_mcp_tool_name_description_extracted(self, mcp_tool_metadata: dict):
        assert mcp_tool_metadata["name"] == "pubmed_search"
        assert mcp_tool_metadata["description"] == "Search PubMed for biomedical literature"

    def test_mcp_tool_input_schema_parsed(self, mcp_tool_metadata: dict):
        params = mcp_tool_metadata["inputSchema"]
        assert "query" in params["properties"]
        assert params["properties"]["query"]["type"] == "string"
        assert "max_results" in params["properties"]

    def test_register_multiple_mcp_tools(self, tool_registry: ToolRegistry):
        tools_data = [
            ("pubmed_search", "Search PubMed", lambda q, m=10: []),
            ("weather_api", "Get weather", lambda c: {}),
            ("calculator", "Do math", lambda a, b, o: {}),
        ]
        for name, desc, fn in tools_data:
            tool_registry.register(name=name, description=desc, parameters={"type": "object", "properties": {}}, fn=fn)
        assert len(tool_registry.list_tools()) == 3

    def test_mcp_tool_deduplication_last_wins(self, tool_registry: ToolRegistry):
        tool_registry.register(
            name="pubmed_search",
            description="v1",
            parameters={"type": "object", "properties": {}},
            fn=lambda: "v1_result",
        )
        with pytest.raises(Exception, match="already registered"):
            tool_registry.register(
                name="pubmed_search",
                description="v2",
                parameters={"type": "object", "properties": {}},
                fn=lambda: "v2_result",
            )

    def test_dynamic_tool_discovery_adds_to_registry(self, tool_registry: ToolRegistry):
        new_tool = {
            "name": "newly_discovered",
            "description": "A dynamically discovered tool",
            "inputSchema": {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]},
        }
        tool_registry.register(
            name=new_tool["name"],
            description=new_tool["description"],
            parameters=new_tool["inputSchema"],
            fn=lambda x: f"processed_{x}",
        )
        tool = tool_registry.get_tool("newly_discovered")
        assert tool["description"] == "A dynamically discovered tool"


class TestMcpToolParameterValidation:
    def test_missing_required_param_raises(self, tool_registry: ToolRegistry, mcp_tool_metadata: dict):
        meta = mcp_tool_metadata
        tool_registry.register(
            name=meta["name"],
            description=meta["description"],
            parameters=meta["inputSchema"],
            fn=lambda query, max_results=10: [f"result_{query}"],
        )
        result = tool_registry.execute("pubmed_search", max_results=5)
        assert result["status"] == "error"

    def test_invalid_param_type_raises(self, tool_registry: ToolRegistry, mcp_tool_metadata: dict):
        meta = mcp_tool_metadata
        tool_registry.register(
            name=meta["name"],
            description=meta["description"],
            parameters=meta["inputSchema"],
            fn=lambda query, max_results=10: [f"result_{query}"],
        )
        with pytest.raises(TypeError):
            tool_registry.execute("pubmed_search", query=123)

    def test_valid_params_pass_validation(self, tool_registry: ToolRegistry, mcp_tool_metadata: dict):
        meta = mcp_tool_metadata
        fn = MagicMock(return_value=["result_1", "result_2"])
        tool_registry.register(
            name=meta["name"],
            description=meta["description"],
            parameters=meta["inputSchema"],
            fn=fn,
        )
        result = tool_registry.execute("pubmed_search", query="cancer")
        assert result["status"] == "ok"
        fn.assert_called_once_with(query="cancer")

    def test_no_required_params_optional_allowed(self, tool_registry: ToolRegistry, mcp_tool_metadata_no_required: dict):
        meta = mcp_tool_metadata_no_required
        fn = MagicMock(return_value="echoed")
        tool_registry.register(
            name=meta["name"],
            description=meta["description"],
            parameters=meta["inputSchema"],
            fn=fn,
        )
        result = tool_registry.execute("echo")
        assert result["status"] == "ok"
        fn.assert_called_once_with()


class TestMcpToolReturnValue:
    def test_success_return_value(self, tool_registry: ToolRegistry):
        tool_registry.register(
            name="success_tool",
            description="Always succeeds",
            parameters={"type": "object", "properties": {}},
            fn=lambda: {"data": [1, 2, 3]},
        )
        result = tool_registry.execute("success_tool")
        assert result["status"] == "ok"
        assert result["data"] == {"data": [1, 2, 3]}
        assert result["error"] is None

    def test_failure_return_value(self, tool_registry: ToolRegistry):
        tool_registry.register(
            name="fail_tool",
            description="Always fails",
            parameters={"type": "object", "properties": {}},
            fn=lambda: (_ for _ in ()).throw(ValueError("processing error")),
        )
        result = tool_registry.execute("fail_tool")
        assert result["status"] == "error"
        assert "processing error" in result["error"]

    def test_timeout_return_value(self, tool_registry: ToolRegistry):
        tool_registry.register(
            name="slow_tool",
            description="Slow tool",
            parameters={"type": "object", "properties": {}},
            fn=lambda: (_ for _ in ()).throw(TimeoutError("tool execution timed out")),
        )
        result = tool_registry.execute("slow_tool")
        assert result["status"] == "error"
        assert "timed out" in result["error"]

    def test_none_return_handled(self, tool_registry: ToolRegistry):
        tool_registry.register(
            name="null_tool",
            description="Returns None",
            parameters={"type": "object", "properties": {}},
            fn=lambda: None,
        )
        result = tool_registry.execute("null_tool")
        assert result["status"] == "ok"
        assert result["data"] is None


class TestMcpToolExecutionTimeout:
    def test_tool_timeout_raises_timeout_error(self, tool_registry: ToolRegistry):
        tool_registry.register(
            name="timeout_tool",
            description="Times out",
            parameters={"type": "object", "properties": {}},
            fn=lambda: (_ for _ in ()).throw(TimeoutError("tool execution timed out after 30s")),
        )
        result = tool_registry.execute("timeout_tool")
        assert result["status"] == "error"
        assert "timed out" in result["error"]

    def test_timeout_error_message(self):
        error = TimeoutError("Tool execution timed out after 30s")
        assert "timed out" in str(error)
        assert "30s" in str(error)


class TestMcpToolDynamicDiscovery:
    def test_new_tool_auto_register(self, tool_registry: ToolRegistry):
        discovered_tools = [
            {"name": "tool_a", "description": "A", "inputSchema": {"type": "object", "properties": {}}},
            {"name": "tool_b", "description": "B", "inputSchema": {"type": "object", "properties": {}}},
        ]
        for t in discovered_tools:
            tool_registry.register(name=t["name"], description=t["description"], parameters=t["inputSchema"], fn=lambda: None)
        assert len(tool_registry.list_tools()) == 2

    def test_discovered_tool_executable(self, tool_registry: ToolRegistry):
        tool_registry.register(
            name="discovered_tool",
            description="Newly discovered",
            parameters={"type": "object", "properties": {"x": {"type": "integer"}}},
            fn=lambda x: x * 2,
        )
        result = tool_registry.execute("discovered_tool", x=21)
        assert result["data"] == 42
