Write the file tests/agent_runtime/test_tool_bridge.py with this exact Python code:

```python
"""Tests for tool_bridge module."""

from cloud.app.agent_runtime.tool_bridge import ToolBridge, ToolResult
from cloud.app.agent_runtime.models import ToolDef


def test_empty_on_init():
    """ToolBridge should have no tools after initialization."""
    tb = ToolBridge()
    assert tb.list_tools() == []


def test_register_default_tools():
    """ToolBridge should register both DEFAULT_TOOLS and BRAIN_TOOLS."""
    tb = ToolBridge()
    tb.register_default_tools()
    tools = tb.list_tools()
    assert len(tools) == 25


def test_register_single_tool():
    """Registering a single ToolDef should add it to the tool list."""
    tb = ToolBridge()
    tool = ToolDef(name="test_tool", description="A test tool", params={}, permission_level="read")
    tb.register_tool(tool)
    tools = tb.list_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "test_tool"
    assert tools[0]["description"] == "A test tool"


def test_tool_result_defaults():
    """ToolResult should have correct default values."""
    result = ToolResult()
    assert result.success is False
    assert result.data is None
    assert result.error == ""


def test_tool_result_custom():
    """ToolResult should accept custom values."""
    result = ToolResult(success=True, data="hello")
    assert result.success is True
    assert result.data == "hello"
```

After writing, run: python -m py_compile tests/agent_runtime/test_tool_bridge.py
