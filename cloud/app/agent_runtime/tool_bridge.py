import json
import sqlite3
import time
import urllib.request
from functools import partial

from cloud.app.agent_runtime.models import ToolDef
from cloud.app.agent_runtime.retry import retry_with_backoff


class ToolRegistry:
    def __init__(self, db):
        self._db = db
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
                params={"endpoint": "/opportunity/bidding/list"},
                endpoint="GET /opportunity/bidding/list",
                permission_level="read",
            ),
            ToolDef(
                name="query_opportunity",
                description="查询商机",
                params={"endpoint": "/opportunity/opportunity/list"},
                endpoint="GET /opportunity/opportunity/list",
                permission_level="read",
            ),
            ToolDef(
                name="query_knowledge_graph",
                description="查询知识图谱",
                params={"endpoint": "/cloud/kg/query"},
                endpoint="GET /cloud/kg/query",
                permission_level="read",
            ),
            ToolDef(
                name="create_notification",
                description="发送通知",
                params={"endpoint": "/cloud/notification/create"},
                endpoint="POST /cloud/notification/create",
                permission_level="write",
            ),
            ToolDef(
                name="analyze_with_llm",
                description="调LLM分析",
                params={"endpoint": "/ai/chat"},
                endpoint="POST /ai/chat",
                permission_level="read",
            ),
            ToolDef(
                name="compliance_check",
                description="合规检查",
                params={"endpoint": "/cloud/compliance/check"},
                endpoint="POST /cloud/compliance/check",
                permission_level="write",
            ),
            ToolDef(
                name="search_memory",
                description="查记忆",
                params={"endpoint": "/memory/recall"},
                endpoint="POST /memory/recall",
                permission_level="read",
            ),
            ToolDef(
                name="write_memory",
                description="写入记忆",
                params={"endpoint": "/memory/entries"},
                endpoint="POST /memory/entries",
                permission_level="write",
            ),
            ToolDef(
                name="query_training_records",
                description="查训练记录",
                params={},
                endpoint="sql:SELECT * FROM coach_session",
                permission_level="read",
            ),
            ToolDef(
                name="query_agent_tasks",
                description="查询Agent执行任务",
                params={},
                endpoint="sql:SELECT * FROM agent_execution_tasks",
                permission_level="read",
            ),
        ]
        brain_tools = [
            ToolDef(
                name="agent_brain_get",
                description="读取Agent自身状态值（短期记忆）",
                params={},
                endpoint="internal:brain_get",
                permission_level="read",
            ),
            ToolDef(
                name="agent_brain_set",
                description="写入Agent自身状态值（短期记忆）",
                params={},
                endpoint="internal:brain_set",
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

        ep = tool.endpoint
        if ep.startswith("internal:"):
            action = ep[len("internal:") :]
            if action == "brain_get":
                data = self._brain.get(params.get("key"), params.get("user_id", 0))
                return {"success": True, "data": data, "error": None}
            if action == "brain_set":
                self._brain.set(params.get("key"), params.get("value"), params.get("user_id", 0))
                return {"success": True, "data": "ok", "error": None}
        if ep.startswith("sql:"):
            return self._call_sql(ep, params, tool_name=tool_name)

        parts = ep.split(" ", 1)
        method = parts[0].upper()
        path = parts[1] if len(parts) > 1 else ""
        url = f"http://localhost:8000{path}"
        data = json.dumps(params).encode("utf-8") if method == "POST" else None
        return self._http_call(url, data, auth_header, tool_name=tool_name, timeout=15)

    def _call_sql(self, endpoint: str, params: dict, tool_name: str = "") -> dict:
        sql = endpoint[len("sql:") :]
        try:
            self._db.execute("PRAGMA busy_timeout=5000")
            cur = self._db.execute(sql)
            rows = cur.fetchall() if cur.description else []
            self._db.commit()
            if tool_name:
                self._failure_counts[tool_name] = 0
            return {"success": True, "data": [dict(r) for r in rows], "error": None}
        except sqlite3.OperationalError as e:
            err_str = str(e)
            if "database is locked" in err_str:
                error_msg = f"SQL timeout: {err_str}"
            else:
                error_msg = err_str
            if tool_name:
                self._failure_counts[tool_name] = self._failure_counts.get(tool_name, 0) + 1
                if self._failure_counts[tool_name] >= 3:
                    self._breaker_expiry[tool_name] = time.time() + 30
            return {"success": False, "data": None, "error": error_msg}
        except Exception as e:
            if tool_name:
                self._failure_counts[tool_name] = self._failure_counts.get(tool_name, 0) + 1
                if self._failure_counts[tool_name] >= 3:
                    self._breaker_expiry[tool_name] = time.time() + 30
            return {"success": False, "data": None, "error": str(e)}

    def _raw_http(self, url: str, data: bytes | None, auth_header: str, timeout: int) -> dict:
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": auth_header,
            },
            method="POST" if data else "GET",
        )
        with urllib.request.urlopen(req, timeout=timeout) as rp:
            raw = rp.read().decode("utf-8")
            return json.loads(raw)

    def _http_call(self, url: str, data: bytes | None, auth_header: str, tool_name: str = "", timeout: int = 15) -> dict:
        fn = partial(self._raw_http, url, data, auth_header, timeout)
        result = retry_with_backoff(fn, max_attempts=3, base_delay=1.0)
        if result["success"]:
            if tool_name:
                self._failure_counts[tool_name] = 0
            return {"success": True, "data": result["data"], "error": None}
        if tool_name:
            self._failure_counts[tool_name] = self._failure_counts.get(tool_name, 0) + 1
            if self._failure_counts[tool_name] >= 3:
                self._breaker_expiry[tool_name] = time.time() + 30
        return {"success": False, "data": None, "error": result["error"]}

    def list_tools(self) -> list[dict]:
        return [{"name": t.name, "description": t.description, "permission_level": t.permission_level} for t in self._tools.values()]
