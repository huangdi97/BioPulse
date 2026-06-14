from __future__ import annotations

from collections import deque
from typing import Any, Callable


class CycleDetectedError(Exception): ...


class DuplicateToolError(Exception): ...


class ToolNotFoundError(Exception): ...


class PortTypeError(Exception): ...


class EDAGNode:
    def __init__(
        self,
        id: str,
        input_port: dict[str, type] | None = None,
        output_port: dict[str, type] | None = None,
    ) -> None:
        self.id = id
        self.input_port = input_port or {}
        self.output_port = output_port or {}
        self.parent: EDAGNode | None = None
        self.children: list[EDAGNode] = []

    def add_child(self, child: EDAGNode) -> None:
        if self._would_cycle(child):
            raise CycleDetectedError(f"Adding {child.id} to {self.id} would create a cycle")
        child.parent = self
        self.children.append(child)

    def _would_cycle(self, node: EDAGNode) -> bool:
        current: EDAGNode | None = self
        while current is not None:
            if current is node:
                return True
            current = current.parent
        return False

    def validate_input(self, data: dict[str, Any]) -> None:
        for key, expected_type in self.input_port.items():
            if key in data:
                value = data[key]
                if not isinstance(value, expected_type):
                    raise PortTypeError(f"Input '{key}' expects {expected_type.__name__}, got {type(value).__name__}")

    def validate_output(self, data: dict[str, Any]) -> None:
        for key, expected_type in self.output_port.items():
            if key in data:
                value = data[key]
                if not isinstance(value, expected_type):
                    raise PortTypeError(f"Output '{key}' expects {expected_type.__name__}, got {type(value).__name__}")

    def dfs(self) -> list[EDAGNode]:
        result: list[EDAGNode] = []
        stack = [self]
        visited: set[str] = set()
        while stack:
            node = stack.pop()
            if node.id in visited:
                continue
            visited.add(node.id)
            result.append(node)
            for child in reversed(node.children):
                stack.append(child)
        return result

    def bfs(self) -> list[EDAGNode]:
        result: list[EDAGNode] = []
        queue: deque[EDAGNode] = deque([self])
        visited: set[str] = set()
        while queue:
            node = queue.popleft()
            if node.id in visited:
                continue
            visited.add(node.id)
            result.append(node)
            for child in node.children:
                queue.append(child)
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "input_port": {k: v.__name__ for k, v in self.input_port.items()},
            "output_port": {k: v.__name__ for k, v in self.output_port.items()},
            "children": [child.to_dict() for child in self.children],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EDAGNode:
        _type_map: dict[str, type] = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "Any": Any,
        }
        node = cls(
            id=data["id"],
            input_port={k: _type_map[v] for k, v in data.get("input_port", {}).items()},
            output_port={k: _type_map[v] for k, v in data.get("output_port", {}).items()},
        )
        for child_data in data.get("children", []):
            child = cls.from_dict(child_data)
            child.parent = node
            node.children.append(child)
        return node


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        fn: Callable[..., Any],
    ) -> None:
        if name in self._tools:
            raise DuplicateToolError(f"Tool '{name}' is already registered")
        self._tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "fn": fn,
        }

    def unregister(self, name: str) -> None:
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool '{name}' not found")
        del self._tools[name]

    def get_tool(self, name: str) -> dict[str, Any]:
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool '{name}' not found")
        return {
            "name": self._tools[name]["name"],
            "description": self._tools[name]["description"],
            "parameters": self._tools[name]["parameters"],
        }

    def list_tools(self) -> list[dict[str, Any]]:
        return sorted(
            [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                }
                for t in self._tools.values()
            ],
            key=lambda x: x["name"],
        )

    def execute(self, name: str, **kwargs: Any) -> dict[str, Any]:
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool '{name}' not found")
        tool = self._tools[name]
        schema = tool["parameters"]
        for param_name, param_schema in schema.get("properties", {}).items():
            if param_name in kwargs:
                expected_type = param_schema.get("type")
                value = kwargs[param_name]
                if expected_type == "string" and not isinstance(value, str):
                    raise TypeError(f"Parameter '{param_name}' expects {expected_type}, got {type(value).__name__}")
                if expected_type == "integer" and not isinstance(value, int):
                    raise TypeError(f"Parameter '{param_name}' expects {expected_type}, got {type(value).__name__}")
                if expected_type == "number" and not isinstance(value, (int, float)):
                    raise TypeError(f"Parameter '{param_name}' expects {expected_type}, got {type(value).__name__}")
        try:
            result = tool["fn"](**kwargs)
            return {"status": "ok", "data": result, "error": None}
        except Exception as e:
            return {"status": "error", "data": None, "error": str(e)}

    def clear(self) -> None:
        self._tools.clear()


class InferenceLoop:
    def __init__(
        self,
        tool_registry: ToolRegistry,
        max_iterations: int = 10,
        step_timeout: float = 30.0,
    ) -> None:
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations
        self.step_timeout = step_timeout
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def run(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not messages:
            return []
        self._running = True
        outputs: list[dict[str, Any]] = []
        try:
            for i, msg in enumerate(messages):
                if not self._running or i >= self.max_iterations:
                    break
                output = self._step(msg)
                outputs.append(output)
                if output.get("type") == "final":
                    self._running = False
                    break
        finally:
            self._running = False
        return outputs

    def stop(self) -> None:
        self._running = False

    def _step(self, msg: dict[str, Any]) -> dict[str, Any]:
        content = msg.get("content", "")
        tool_calls = msg.get("tool_calls", [])

        if not content and not tool_calls:
            return {"type": "output", "content": ""}

        for tc in tool_calls:
            try:
                result = self.tool_registry.execute(tc["name"], **tc.get("arguments", {}))
                if result["status"] == "error":
                    return {
                        "type": "error",
                        "content": result["error"],
                        "tool": tc["name"],
                    }
            except Exception as e:
                return {"type": "error", "content": str(e), "tool": tc["name"]}

        return {"type": "output", "content": content}
