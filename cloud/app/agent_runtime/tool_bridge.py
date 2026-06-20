"""工具桥接模块，注册工具、权限校验、调用转发及熔断保护。"""

from __future__ import annotations

import json
import logging
import time
import urllib.request
from typing import Any

from cloud.app.agent_runtime.models import ToolDef
from cloud.app.agent_runtime.retry import retry_with_backoff
from cloud.app.agent_runtime.telemetry import trace_step
from cloud.app.agent_runtime.tool_bridge_defaults import BRAIN_TOOLS, DEFAULT_TOOLS
from cloud.app.agent_runtime.tool_bridge_sandbox import run_sandboxed
from cloud.app.agent_runtime.tool_bridge_utils import (
    ToolResult,
    check_idempotency,
    format_error,
    idempotency_key,
    set_idempotency,
)
from shared.app_settings import settings

logger = logging.getLogger(__name__)


class ToolBridge:
    """工具注册中心，管理工具定义、权限校验、调用转发与熔断恢复。"""

    def __init__(self):
        """初始化工具注册中心和熔断状态。"""
        self._tools: dict[str, ToolDef] = {}
        self._brain = None
        self._failure_counts: dict[str, int] = {}
        self._breaker_expiry: dict[str, float] = {}
        self._idempotency_cache: dict[str, tuple[float, Any]] = {}
        self._IDEMPOTENCY_TTL = 3600  # 1 hour

    @staticmethod
    def _validate_param(value: Any, expected_type: str, param_name: str) -> str | None:
        """校验单个参数的类型和格式。返回错误信息或 None。"""
        if expected_type == "str" and not isinstance(value, str):
            return f"parameter '{param_name}' expected str, got {type(value).__name__}"
        if expected_type == "int" and not isinstance(value, int):
            return f"parameter '{param_name}' expected int, got {type(value).__name__}"
        if expected_type == "float" and not isinstance(value, (int, float)):
            return f"parameter '{param_name}' expected float, got {type(value).__name__}"
        if expected_type == "bool" and not isinstance(value, bool):
            return f"parameter '{param_name}' expected bool, got {type(value).__name__}"
        if expected_type == "list" and not isinstance(value, list):
            return f"parameter '{param_name}' expected list, got {type(value).__name__}"
        if expected_type == "dict" and not isinstance(value, dict):
            return f"parameter '{param_name}' expected dict, got {type(value).__name__}"
        return None

    def _validate_params(self, tool_name: str, params: dict) -> str | None:
        """根据 ToolDef.params schema 校验参数。返回第一个错误或 None。"""
        tool = self._tools.get(tool_name)
        if tool is None:
            return None
        schema = tool.params
        if not schema or not isinstance(schema, dict):
            return None
        for param_name, expected_type in schema.items():
            if param_name not in params:
                continue  # 可选参数
            err = self._validate_param(params[param_name], expected_type, param_name)
            if err:
                return err
        return None

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

    def _check_permission(
        self,
        tool: ToolDef,
        tool_name: str,
        params: dict,
        caller_permission: str,
    ) -> dict | None:
        level_order = {"read": 0, "write": 1, "admin": 2}
        if level_order.get(tool.permission_level, 0) > level_order.get(caller_permission, 0):
            return format_error(f"permission denied: {tool_name} requires {tool.permission_level}, caller has {caller_permission}")
        if level_order.get(tool.permission_level, 0) >= 1:
            return {
                "success": False,
                "data": None,
                "needs_approval": True,
                "tool": tool_name,
                "params": params,
            }
        return None

    def _call_http_tool(
        self,
        tool_name: str,
        params: dict,
        auth_header: str,
        idempotency_agent: str | None,
        idempotency_step: int,
        trace_id: str = "",
    ) -> dict:
        url = f"{settings.cloud_api_base}/agent-gateway/execute"
        payload = {"tool_name": tool_name, "params": params}
        data = json.dumps(payload).encode("utf-8")

        def _do_post():
            """执行 HTTP POST 请求并返回 JSON 结果。"""
            headers = {
                "Content-Type": "application/json",
                "Authorization": auth_header,
            }
            if trace_id:
                headers["X-BioPulse-Trace-Id"] = trace_id
            req = urllib.request.Request(
                url,
                data=data,
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=settings.tool_timeout_seconds) as rp:
                raw = rp.read().decode("utf-8")
                try:
                    return json.loads(raw)
                except json.JSONDecodeError as e:
                    return {"success": False, "data": None, "error": f"invalid JSON response: {e}"}

        try:
            result = retry_with_backoff(_do_post, max_attempts=3, base_delay=1.0)
        except Exception as e:
            logger.error("HTTP tool call %s failed after retries: %s", tool_name, e)
            self._failure_counts[tool_name] = self._failure_counts.get(tool_name, 0) + 1
            if self._failure_counts[tool_name] >= 3:
                self._breaker_expiry[tool_name] = time.time() + 30
            return format_error(f"tool call failed: {e}")
        if result["success"]:
            self._failure_counts[tool_name] = 0
            ret = {"success": True, "data": result["data"], "error": None}
            if idempotency_agent:
                set_idempotency(
                    self._idempotency_cache,
                    idempotency_key(idempotency_agent, tool_name, idempotency_step),
                    ret,
                )
            return ret
        self._failure_counts[tool_name] = self._failure_counts.get(tool_name, 0) + 1
        if self._failure_counts[tool_name] >= 3:
            self._breaker_expiry[tool_name] = time.time() + 30
        return {"success": False, "data": None, "error": result["error"]}

    def _route_tool(
        self,
        tool: ToolDef,
        tool_name: str,
        params: dict,
        auth_header: str,
        idempotency_agent: str | None,
        idempotency_step: int,
        trace_id: str = "",
    ) -> dict:
        if tool.sandbox:
            return run_sandboxed(tool_name, params, idempotency_agent, idempotency_step, self._idempotency_cache)

        if tool_name == "agent_brain_get":
            data = self._brain.get(params.get("key"), params.get("user_id", 0))
            result = {"success": True, "data": data, "error": None}
            if idempotency_agent:
                set_idempotency(
                    self._idempotency_cache,
                    idempotency_key(idempotency_agent, tool_name, idempotency_step),
                    result,
                )
            return result
        if tool_name == "agent_brain_set":
            self._brain.set(params.get("key"), params.get("value"), params.get("user_id", 0))
            result = {"success": True, "data": "ok", "error": None}
            if idempotency_agent:
                set_idempotency(
                    self._idempotency_cache,
                    idempotency_key(idempotency_agent, tool_name, idempotency_step),
                    result,
                )
            return result

        return self._call_http_tool(
            tool_name,
            params,
            auth_header,
            idempotency_agent,
            idempotency_step,
            trace_id,
        )

    def call(
        self,
        tool_name: str,
        params: dict,
        auth_header: str,
        caller_permission: str = "read",
        idempotency_agent: str | None = None,
        idempotency_step: int = 0,
        trace_id: str = "",
    ) -> dict:
        """执行工具调用，包含权限校验、熔断检查、参数校验、幂等性和重试。"""
        now = time.time()
        if tool_name in self._breaker_expiry:
            if now < self._breaker_expiry[tool_name]:
                return format_error(f"circuit breaker open for {tool_name}")
            else:
                del self._breaker_expiry[tool_name]
                self._failure_counts.pop(tool_name, None)

        tool = self._tools.get(tool_name)
        if tool is None:
            return format_error(f"unknown tool: {tool_name}")

        param_err = self._validate_params(tool_name, params)
        if param_err:
            return format_error(param_err)

        if idempotency_agent:
            idem_key = idempotency_key(
                idempotency_agent,
                tool_name,
                idempotency_step,
            )
            cached = check_idempotency(self._idempotency_cache, idem_key, self._IDEMPOTENCY_TTL)
            if cached is not None:
                return cached

        perm_result = self._check_permission(
            tool,
            tool_name,
            params,
            caller_permission,
        )
        if perm_result is not None:
            return perm_result

        return self._route_tool(
            tool,
            tool_name,
            params,
            auth_header,
            idempotency_agent,
            idempotency_step,
            trace_id,
        )

    def execute(self, tool_name: str, args: dict[str, Any] | None = None, caller_agent_id: str | None = None) -> ToolResult:
        """执行工具调用，含 caller_agent_id 白名单校验。

        allowed_agents 为空列表时允许所有 Agent 调用。
        """
        with trace_step("execute_tool", {"tool": tool_name}):
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
