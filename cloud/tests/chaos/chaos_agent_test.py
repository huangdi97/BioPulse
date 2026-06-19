"""混沌/故障注入工具 — 用于测试 Agent 在故障下的降级与隔离行为。"""

from unittest.mock import patch

from cloud.app.agent_runtime.execution_loop import (
    AllModelsFailedError,
)
from cloud.app.agent_runtime.tool_bridge import ToolBridge


def inject_db_failure():
    """模拟数据库断连故障。patch AgentRegistry.get 抛出连接异常。"""

    def _raise_db_error(*args, **kwargs):
        raise ConnectionError("DB connection refused - simulated failure")

    return patch(
        "cloud.app.agent_runtime.execution_loop.AgentRegistry.get",
        side_effect=_raise_db_error,
    )


def inject_api_timeout():
    """模拟 LLM API 超时故障。patch 使得所有 LLM provider 均失败。"""

    def _raise_llm_failed(*args, **kwargs):
        raise AllModelsFailedError([{"provider": "deepseek", "model": "deepseek-v4-flash", "error": "timeout", "elapsed": 60.0}])

    return patch(
        "cloud.app.agent_runtime.execution_loop.AgentRegistry.get",
        side_effect=_raise_llm_failed,
    )


def inject_rate_limit():
    """模拟限流触发。patch ToolBridge.execute 返回限流错误。"""

    def _rate_limited_execute(self, tool_name, args, caller_agent_id=None):
        return {"success": False, "error": "rate_limit_exceeded: too many requests", "data": None}

    return patch.object(
        ToolBridge,
        "execute",
        autospec=True,
        side_effect=_rate_limited_execute,
    )
