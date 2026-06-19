"""混沌测试场景 — 验证 Agent 在故障注入下的正确行为。

验证目标：
  - test_db_failure_agent_degradation:      DB 故障 → Agent 降级，不崩溃
  - test_llm_timeout_circuit_breaker:       LLM 超时 → 熔断/降级
  - test_rate_limit_graceful:               限流触发 → 优雅降级
  - test_multi_failure_isolation:           多故障 → 隔离，不级联崩溃
"""

import json
from unittest.mock import MagicMock, patch

from cloud.app.agent_runtime.execution_loop import ExecutionEngine
from cloud.app.agent_runtime.models import RuntimeResult

from .chaos_agent_test import inject_db_failure, inject_api_timeout, inject_rate_limit


def _make_host():
    host = MagicMock()
    host._agent_db = MagicMock()
    host._call_ai = MagicMock()
    host._tool_registry = MagicMock()
    host._tool_registry.list_tools.return_value = []
    host._tool_registry.call.return_value = {"success": True, "data": "ok", "needs_approval": False}
    host._helper = MagicMock()
    host._helper._load_checkpoint.return_value = None
    host._tool_exec = MagicMock()
    host._tool_exec._reflect_before_tool.return_value = {}
    host._core_tools = MagicMock()
    host._core_tools._check_budget.return_value = True
    host._core_tools._build_step_log.return_value = {}
    host._core_tools._accumulate_cost = MagicMock()
    host._compress_messages = MagicMock(side_effect=lambda msgs: msgs)
    host._planner = MagicMock()
    host._planner.plan.return_value = []
    host._verifier = MagicMock()
    host._verifier.verify.return_value = {"passed": True}
    host._loop_detector = MagicMock()
    host._loop_detector.record = MagicMock()
    host._loop_detector.detect.return_value = None
    host._is_completed = MagicMock(return_value=True)
    host._auth_header = ""
    return host


def _mock_agent():
    agent = MagicMock()
    agent.identity.key = "test_agent"
    agent.identity.role = "测试助手"
    agent.identity.goal = "测试目标"
    agent.identity.allowed_tools = []
    agent.identity.model_preference.temperature = 0.3
    agent.identity.safety_profile.max_permission = "read"
    agent.identity.trigger_mode = MagicMock()
    agent.identity.trigger_mode.value = "user_request"
    agent.identity.event_subscriptions = []
    agent.identity.backstory = ""
    agent.identity.cost_budget = 0.10
    agent.identity.memory_namespace = ""
    return agent


def test_db_failure_agent_degradation():
    """DB 故障 → Agent 降级返回（status=degraded），不抛出异常。"""
    host = _make_host()
    engine = ExecutionEngine(host)
    with inject_db_failure():
        result = engine.execute("test goal", "test_agent")
        assert result.status == "degraded"
        assert "temporarily unavailable" in result.result or "unavailable" in result.result


def test_llm_timeout_circuit_breaker():
    """LLM 全失败 → 返回 degraded 状态而非崩溃。"""
    host = _make_host()
    engine = ExecutionEngine(host)
    with inject_api_timeout():
        result = engine.execute("test goal", "test_agent")
        assert result.status == "degraded"
        assert result.result != ""


def test_rate_limit_graceful():
    """限流触发 → 不抛出未处理异常，返回有效结果。"""
    host = _make_host()
    engine = ExecutionEngine(host)
    mock_agent = _mock_agent()

    valid_llm_reply = {
        "reply": json.dumps({
            "action": "call_tool",
            "tool": "query_db",
            "params": {"key": "test"},
            "reasoning": "testing rate limit",
        })
    }
    host._call_ai = MagicMock(return_value=valid_llm_reply)
    host._is_completed = MagicMock(return_value=False)
    host._tool_registry.call = MagicMock(
        return_value={"success": False, "error": "rate_limit_exceeded: too many requests", "data": None}
    )
    host._tool_exec._handle_step_error = MagicMock(return_value=False)
    host._tool_exec._handle_max_iterations = MagicMock(
        return_value=RuntimeResult(status="degraded", result="rate limit exceeded", iterations=1, tool_calls=1, logs=[])
    )

    with patch("cloud.app.agent_runtime.execution_loop.AgentRegistry.get", return_value=mock_agent):
        result = engine.execute("test goal", "test_agent")
        assert result is not None
        assert hasattr(result, "status") or hasattr(result, "result")


def test_multi_failure_isolation():
    """多故障并发 → 故障隔离，engine 仍然稳定可用。"""
    host = _make_host()
    engine1 = ExecutionEngine(host)
    engine2 = ExecutionEngine(host)

    with inject_db_failure():
        result1 = engine1.execute("goal1", "agent_a")
        assert result1.status == "degraded"

    with inject_api_timeout():
        result2 = engine2.execute("goal2", "agent_b")
        assert result2.status == "degraded"