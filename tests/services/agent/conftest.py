from collections.abc import Generator
from typing import Any

import pytest

from cloud.app.services.agent_core import EDAGNode, InferenceLoop, ToolRegistry


@pytest.fixture
def edag_node() -> EDAGNode:
    root = EDAGNode(id="root", input_port={"val": str}, output_port={"result": str})
    child1 = EDAGNode(id="child1", input_port={"val": str}, output_port={"result": str})
    child2 = EDAGNode(id="child2", input_port={"val": str}, output_port={"result": str})
    grandchild = EDAGNode(id="grandchild", input_port={"val": str}, output_port={"result": str})
    root.add_child(child1)
    root.add_child(child2)
    child1.add_child(grandchild)
    return root


@pytest.fixture
def tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        name="calculator",
        description="Perform arithmetic calculations",
        parameters={
            "type": "object",
            "properties": {
                "a": {"type": "number"},
                "b": {"type": "number"},
                "op": {"type": "string"},
            },
            "required": ["a", "b", "op"],
        },
        fn=lambda a, b, op: {"result": eval(f"{a}{op}{b}")},
    )
    registry.register(
        name="weather",
        description="Get weather for a city",
        parameters={
            "type": "object",
            "properties": {
                "city": {"type": "string"},
            },
            "required": ["city"],
        },
        fn=lambda city: {"temperature": 22, "condition": "sunny"},
    )
    registry.register(
        name="search",
        description="Search the web",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["query"],
        },
        fn=lambda query, limit=10: [f"result_{i}" for i in range(limit)],
    )
    return registry


@pytest.fixture
def inference_loop(tool_registry: ToolRegistry) -> InferenceLoop:
    return InferenceLoop(tool_registry=tool_registry, max_iterations=10, step_timeout=30.0)


@pytest.fixture
def mock_tool_response() -> dict[str, Any]:
    return {"status": "ok", "data": {"result": 42}, "error": None}


@pytest.fixture(autouse=True)
def clean_registry() -> Generator[None, None, None]:
    yield


def make_tool_registry() -> ToolRegistry:
    return ToolRegistry()
