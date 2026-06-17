import pytest
from cloud.app.services.agent_core import (
    DuplicateToolError,
    ToolNotFoundError,
    ToolRegistry,
)


class TestToolRegistryRegister:
    def test_register_tool_success(self, tool_registry: ToolRegistry) -> None:
        tool_registry.register(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {}},
            fn=lambda: "done",
        )
        tool = tool_registry.get_tool("test_tool")
        assert tool["name"] == "test_tool"
        assert tool["description"] == "A test tool"

    def test_register_duplicate_name_raises(self, tool_registry: ToolRegistry) -> None:
        with pytest.raises(DuplicateToolError, match="is already registered"):
            tool_registry.register(
                name="calculator",
                description="Duplicate",
                parameters={"type": "object", "properties": {}},
                fn=lambda: None,
            )

    def test_register_duplicate_custom_message(self) -> None:
        registry = ToolRegistry()

        def fn():
            return None

        registry.register("dup", "first", {"type": "object", "properties": {}}, fn)
        with pytest.raises(DuplicateToolError, match="dup"):
            registry.register("dup", "second", {"type": "object", "properties": {}}, fn)

    def test_register_multiple_tools_distinct(self, tool_registry: ToolRegistry) -> None:
        assert len(tool_registry.list_tools()) == 3


class TestToolRegistryUnregister:
    def test_unregister_removes_tool(self, tool_registry: ToolRegistry) -> None:
        tool_registry.unregister("calculator")
        with pytest.raises(ToolNotFoundError):
            tool_registry.get_tool("calculator")

    def test_unregister_nonexistent_raises(self, tool_registry: ToolRegistry) -> None:
        with pytest.raises(ToolNotFoundError, match="not found"):
            tool_registry.unregister("nonexistent")

    def test_unregister_reduces_list(self, tool_registry: ToolRegistry) -> None:
        tool_registry.unregister("weather")
        names = [t["name"] for t in tool_registry.list_tools()]
        assert "weather" not in names

    def test_unregister_all_leaves_empty(self, tool_registry: ToolRegistry) -> None:
        for name in ["calculator", "weather", "search"]:
            tool_registry.unregister(name)
        assert tool_registry.list_tools() == []


class TestToolRegistryQuery:
    def test_get_tool_returns_metadata(self, tool_registry: ToolRegistry) -> None:
        tool = tool_registry.get_tool("weather")
        assert tool["name"] == "weather"
        assert tool["description"] == "Get weather for a city"

    def test_get_tool_returns_parameters_schema(self, tool_registry: ToolRegistry) -> None:
        tool = tool_registry.get_tool("search")
        assert "query" in tool["parameters"]["properties"]

    def test_get_tool_nonexistent_raises(self, tool_registry: ToolRegistry) -> None:
        with pytest.raises(ToolNotFoundError):
            tool_registry.get_tool("does_not_exist")

    def test_get_tool_does_not_expose_fn(self, tool_registry: ToolRegistry) -> None:
        tool = tool_registry.get_tool("calculator")
        assert "fn" not in tool

    def test_list_tools_returns_all(self, tool_registry: ToolRegistry) -> None:
        tools = tool_registry.list_tools()
        assert len(tools) == 3

    def test_list_tools_sorted_alphabetically(self, tool_registry: ToolRegistry) -> None:
        tools = tool_registry.list_tools()
        names = [t["name"] for t in tools]
        assert names == sorted(names)


class TestToolRegistryExecute:
    def test_execute_returns_ok_status(self, tool_registry: ToolRegistry) -> None:
        result = tool_registry.execute("calculator", a=3, b=4, op="+")
        assert result["status"] == "ok"
        assert result["error"] is None

    def test_execute_returns_data(self, tool_registry: ToolRegistry) -> None:
        result = tool_registry.execute("weather", city="London")
        assert result["data"]["temperature"] == 22
        assert result["data"]["condition"] == "sunny"

    def test_execute_nonexistent_raises(self, tool_registry: ToolRegistry) -> None:
        with pytest.raises(ToolNotFoundError):
            tool_registry.execute("ghost_tool")

    def test_execute_validates_string_param(self, tool_registry: ToolRegistry) -> None:
        with pytest.raises(TypeError, match="expects string, got int"):
            tool_registry.execute("weather", city=123)

    def test_execute_validates_integer_param(self, tool_registry: ToolRegistry) -> None:
        with pytest.raises(TypeError, match="expects integer, got str"):
            tool_registry.execute("search", query="test", limit="ten")

    def test_execute_function_error_returns_error_status(self, tool_registry: ToolRegistry) -> None:
        tool_registry.register(
            name="broken",
            description="Always fails",
            parameters={"type": "object", "properties": {}},
            fn=lambda: (_ for _ in ()).throw(ValueError("something broke")),
        )
        result = tool_registry.execute("broken")
        assert result["status"] == "error"
        assert "something broke" in result["error"]


class TestToolRegistryEmptyState:
    def test_list_empty_returns_empty_list(self) -> None:
        registry = ToolRegistry()
        assert registry.list_tools() == []

    def test_get_tool_empty_raises(self) -> None:
        registry = ToolRegistry()
        with pytest.raises(ToolNotFoundError):
            registry.get_tool("anything")

    def test_unregister_empty_raises(self) -> None:
        registry = ToolRegistry()
        with pytest.raises(ToolNotFoundError):
            registry.unregister("anything")

    def test_execute_empty_raises(self) -> None:
        registry = ToolRegistry()
        with pytest.raises(ToolNotFoundError):
            registry.execute("anything")


class TestToolRegistryClear:
    def test_clear_removes_all_tools(self, tool_registry: ToolRegistry) -> None:
        tool_registry.clear()
        assert tool_registry.list_tools() == []

    def test_clear_then_register_succeeds(self, tool_registry: ToolRegistry) -> None:
        tool_registry.clear()
        tool_registry.register(
            name="new_tool",
            description="After clear",
            parameters={"type": "object", "properties": {}},
            fn=lambda: None,
        )
        assert tool_registry.get_tool("new_tool")["name"] == "new_tool"
