import json
import time
import urllib.request

from cloud.app.agent_runtime.models import ToolDef
from cloud.app.agent_runtime.retry import retry_with_backoff


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDef] = {}
        self._brain = None
        self._failure_counts: dict[str, int] = {}
        self._breaker_expiry: dict[str, float] = {}

    def register_tool(self, tool: ToolDef) -> None:
        tool.permission_level = getattr(tool, "permission_level", "read")
        self._tools[tool.name] = tool

    def set_brain(self, brain):
        self._brain = brain

    def register_default_tools(self) -> None:
        defaults = [
            ToolDef(
                name="query_bidding",
                description="查询招标信息",
                params={},
                permission_level="read",
            ),
            ToolDef(
                name="query_opportunity",
                description="查询商机",
                params={},
                permission_level="read",
            ),
            ToolDef(
                name="query_knowledge_graph",
                description="查询知识图谱",
                params={},
                permission_level="read",
            ),
            ToolDef(
                name="create_notification",
                description="发送通知",
                params={},
                permission_level="write",
            ),
            ToolDef(
                name="analyze_with_llm",
                description="调LLM分析",
                params={},
                permission_level="read",
            ),
            ToolDef(
                name="compliance_check",
                description="合规检查",
                params={},
                permission_level="write",
            ),
            ToolDef(
                name="search_memory",
                description="查记忆",
                params={},
                permission_level="read",
            ),
            ToolDef(
                name="write_memory",
                description="写入记忆",
                params={},
                permission_level="write",
            ),
        ]
        brain_tools = [
            ToolDef(
                name="agent_brain_get",
                description="读取Agent自身状态值（短期记忆）",
                params={},
                permission_level="read",
            ),
            ToolDef(
                name="agent_brain_set",
                description="写入Agent自身状态值（短期记忆）",
                params={},
                permission_level="write",
            ),
        ]
        for t in defaults + brain_tools:
            self.register_tool(t)

    def call(self, tool_name: str, params: dict, auth_header: str, caller_permission: str = "read") -> dict:
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

        url = "http://localhost:8000/agent-gateway/execute"
        payload = {"tool_name": tool_name, "params": params}
        data = json.dumps(payload).encode("utf-8")

        def _do_post():
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

    def list_tools(self) -> list[dict]:
        return [{"name": t.name, "description": t.description, "permission_level": t.permission_level} for t in self._tools.values()]
