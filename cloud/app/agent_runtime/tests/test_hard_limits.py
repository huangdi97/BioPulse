"""Tests for hard limits in ExecutionEngine — LLM calls, timeout, and max iterations."""

import time
from unittest.mock import MagicMock, patch

from cloud.app.agent_runtime.lifecycle.execution_loop import ExecutionEngine


def _make_host():
    host = MagicMock()
    host._agent_db = MagicMock()
    host._helper._load_checkpoint.return_value = None
    host._planner.plan.return_value = {}
    host._tool_registry.list_tools.return_value = []
    host._compress_messages.side_effect = lambda msgs: msgs
    host._core_tools._check_budget.return_value = True
    host._core_tools._accumulate_cost.return_value = None
    host._core_tools._llm_meta.return_value = {}
    host._core_tools._build_step_log.return_value = {}
    host._verifier.verify.return_value = True
    host._tool_exec._handle_step_error.return_value = False
    host._tool_exec._append_invalid_step.return_value = None
    host._tool_exec._save_step_checkpoint.return_value = None
    host._tool_exec._reflect_before_tool.return_value = {}
    host._is_completed.return_value = False
    host._loop_detector.record.return_value = None
    host._loop_detector.detect.return_value = None
    host._auth_header = {}
    host._call_ai.side_effect = lambda *a, **kw: {"reply": "{}"}
    return host


def _mock_agent():
    agent = MagicMock()
    agent.identity.role = "助手"
    agent.identity.goal = "帮助用户"
    agent.identity.allowed_tools = []
    agent.identity.model_preference.temperature = 0.7
    agent.identity.safety_profile.max_permission = "read"
    agent.identity.trigger_mode.value = "manual"
    agent.identity.event_subscriptions = []
    return agent


def test_max_llm_calls_enforced():
    with (
        patch.object(ExecutionEngine, "MAX_LLM_CALLS", 2),
        patch("cloud.app.agent_runtime.execution_loop.AgentRegistry.get", return_value=_mock_agent()),
        patch("cloud.app.agent_runtime.execution_loop.Validator.validate", return_value=(None, "mock error")),
    ):
        host = _make_host()
        engine = ExecutionEngine(host)
        result = engine._execute_impl("test goal", "test_agent")
        assert result.status == "llm_limit_exceeded"


def test_max_execution_timeout():
    with (
        patch.object(ExecutionEngine, "MAX_EXECUTION_SECONDS", 1),
        patch("cloud.app.agent_runtime.execution_loop.AgentRegistry.get", return_value=_mock_agent()),
        patch("cloud.app.agent_runtime.execution_loop.Validator.validate", return_value=(None, "mock error")),
    ):
        host = _make_host()
        host._call_ai.side_effect = lambda *a, **kw: time.sleep(2) or {"reply": "{}"}
        engine = ExecutionEngine(host)
        result = engine._execute_impl("test goal", "test_agent")
        assert result.status == "timeout"


def test_max_iterations_15():
    spec = {
        "role_desc": "你是助手，帮助用户",
        "allowed_tools": [],
        "max_iterations": 20,
        "default_temperature": 0.7,
        "max_permission": "read",
        "trigger_cron": None,
        "trigger_mode": "manual",
        "event_subscriptions": [],
    }
    with (
        patch.object(ExecutionEngine, "MAX_LLM_CALLS", 100),
        patch("cloud.app.agent_runtime.execution_loop.AgentRegistry.get", return_value=_mock_agent()),
        patch("cloud.app.agent_runtime.execution_loop._identity_to_spec", return_value=spec),
        patch("cloud.app.agent_runtime.execution_loop.Validator.validate", return_value=(None, "mock error")),
    ):
        host = _make_host()
        engine = ExecutionEngine(host)
        engine._execute_impl("test goal", "test_agent")
        assert host._call_ai.call_count == 15
