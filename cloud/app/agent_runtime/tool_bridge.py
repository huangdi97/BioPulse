"""工具桥接模块，注册工具、权限校验、调用转发及熔断保护。"""

from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass
from typing import Any

from cloud.app.agent_runtime.models import ToolDef
from cloud.app.agent_runtime.retry import retry_with_backoff
from cloud.app.agent_runtime.tool_bridge_defaults import BRAIN_TOOLS, DEFAULT_TOOLS
from shared.app_settings import settings


@dataclass
class ToolResult:
    """工具执行结果。"""

    success: bool = False
    data: Any = None
    error: str = ""


class ToolBridge:
    """工具注册中心，管理工具定义、权限校验、调用转发与熔断恢复。"""

    def __init__(self):
        """初始化工具注册中心和熔断状态。"""
        self._tools: dict[str, ToolDef] = {}
        self._brain = None
        self._failure_counts: dict[str, int] = {}
        self._breaker_expiry: dict[str, float] = {}

    def register_tool(self, tool: ToolDef) -> None:
        """注册一个工具定义到注册中心。"""
        tool.permission_level = getattr(tool, "permission_level", "read")
        self._tools[tool.name] = tool

    def set_brain(self, brain):
        """设置 Brain 引用以支持 Agent 内部状态读写。"""
        self._brain = brain

    def register_default_tools(self) -> None:
        """注册默认的工具集合，包含业务工具和 Agent 脑工具。"""
        for t in DEFAULT_TOOLS + BRAIN_TOOLS:
            self.register_tool(t)

    def call(self, tool_name: str, params: dict, auth_header: str, caller_permission: str = "read") -> dict:
        """执行工具调用，包含权限校验、熔断检查和重试。"""
        now = time.time()
        if tool_name in self._breaker_expiry:
            if now < self._breaker_expiry[tool_name]:
                return {"success": False, "data": None, "error": f"circuit breaker open for {tool_name}", "needs_approval": False}
            else:
                del self._breaker_expiry[tool_name]
                self._failure_counts.pop(tool_name, None)

        tool = self._tools.get(tool_name)
        if tool is None:
            return {"success": False, "data": None, "error": f"unknown tool: {tool_name}", "needs_approval": False}

        level_order = {"read": 0, "write": 1, "admin": 2}
        if level_order.get(tool.permission_level, 0) > level_order.get(caller_permission, 0):
            return {
                "success": False,
                "data": None,
                "error": f"permission denied: {tool_name} requires {tool.permission_level}, caller has {caller_permission}",
                "needs_approval": False,
            }

        if level_order.get(tool.permission_level, 0) >= 1:
            return {"success": False, "data": None, "needs_approval": True, "tool": tool_name, "params": params}

        if tool_name == "agent_brain_get":
            data = self._brain.get(params.get("key"), params.get("user_id", 0))
            return {"success": True, "data": data, "error": None}
        if tool_name == "agent_brain_set":
            self._brain.set(params.get("key"), params.get("value"), params.get("user_id", 0))
            return {"success": True, "data": "ok", "error": None}

        url = f"{settings.cloud_api_base}/agent-gateway/execute"
        payload = {"tool_name": tool_name, "params": params}
        data = json.dumps(payload).encode("utf-8")

        def _do_post():
            """执行 HTTP POST 请求并返回 JSON 结果。"""
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": auth_header,
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as rp:
                raw = rp.read().decode("utf-8")
                return json.loads(raw)

        result = retry_with_backoff(_do_post, max_attempts=3, base_delay=1.0)
        if result["success"]:
            self._failure_counts[tool_name] = 0
            return {"success": True, "data": result["data"], "error": None}
        self._failure_counts[tool_name] = self._failure_counts.get(tool_name, 0) + 1
        if self._failure_counts[tool_name] >= 3:
            self._breaker_expiry[tool_name] = time.time() + 30
        return {"success": False, "data": None, "error": result["error"]}

    def execute(self, tool_name: str, args: dict[str, Any] | None = None, caller_agent_id: str | None = None) -> ToolResult:
        """执行工具调用，含 caller_agent_id 白名单校验。

        allowed_agents 为空列表时允许所有 Agent 调用。
        """
        tool = self._tools.get(tool_name)
        if tool is None:
            return ToolResult(success=False, error=f"unknown tool: {tool_name}")

        if caller_agent_id is not None and tool.allowed_agents:
            if caller_agent_id not in tool.allowed_agents:
                return ToolResult(success=False, error="agent not allowed")

        return ToolResult(success=True, data=None, error="")

    def list_tools(self) -> list[dict]:
        """返回所有已注册工具的列表。"""
        return [{"name": t.name, "description": t.description, "permission_level": t.permission_level} for t in self._tools.values()]


ToolRegistry = ToolBridge
