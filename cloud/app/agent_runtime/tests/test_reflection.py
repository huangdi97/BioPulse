from unittest.mock import MagicMock

from cloud.app.agent_runtime.core.models import CheckResult, VerificationResult
from cloud.app.agent_runtime.core.planner import Plan, PlanStep
from cloud.app.agent_runtime.lifecycle.execution_loop import ExecutionEngine


def _make_engine(host=None):
    host = host or MagicMock()
    host._planner.generate_plan.return_value = Plan(goal="", steps=[], plan_confidence=0.0)
    host._tool_registry.list_tools.return_value = []
    host._helper._load_checkpoint.return_value = None
    host._planner.plan.return_value = {"step": -1, "action": "plan"}
    return ExecutionEngine(host)


def test_plan_generated_and_injected():
    plan = Plan(
        goal="test goal",
        steps=[
            PlanStep(step_id="s1", description="查询数据", tool="query_tool", params_template={}, dependencies=[]),
            PlanStep(step_id="s2", description="分析结果", tool="analyze_tool", params_template={}, dependencies=["s1"]),
        ],
        completion_conditions=["数据已分析"],
        plan_confidence=0.85,
    )
    host = MagicMock()
    host._planner.generate_plan.return_value = plan
    host._tool_registry.list_tools.return_value = [{"name": "query_tool", "description": ""}, {"name": "analyze_tool", "description": ""}]
    host._helper._load_checkpoint.return_value = None
    host._planner.plan.return_value = {"step": -1, "action": "plan"}
    engine = ExecutionEngine(host)
    spec = {
        "role_desc": "数据助手",
        "allowed_tools": ["query_tool", "analyze_tool"],
        "max_iterations": 10,
        "default_temperature": 0.7,
    }
    c = engine._new_context("test goal", "test_agent", {}, spec)
    host._planner.generate_plan.assert_called_once_with("test goal", ["query_tool", "analyze_tool"], {})
    system_msg = c["messages"][0]["content"]
    assert "你的计划：" in system_msg
    assert "步骤1: 查询数据 — 工具：query_tool" in system_msg
    assert "步骤2: 分析结果 — 工具：analyze_tool" in system_msg
    assert "完成条件：" in system_msg
    assert c["_plan"] is plan
    assert c["_plan_step_index"] == 0


def test_plan_fallback_on_empty():
    host = MagicMock()
    host._planner.generate_plan.return_value = Plan(goal="test", steps=[], plan_confidence=0.0)
    host._tool_registry.list_tools.return_value = []
    host._helper._load_checkpoint.return_value = None
    host._planner.plan.return_value = {"step": -1, "action": "plan"}
    engine = ExecutionEngine(host)
    spec = {
        "role_desc": "助手",
        "allowed_tools": ["tool_a"],
        "max_iterations": 10,
        "default_temperature": 0.7,
    }
    c = engine._new_context("test", "test_agent", {}, spec)
    system_msg = c["messages"][0]["content"]
    assert "你的计划：" not in system_msg
    assert "可用工具" in system_msg
    assert c["_plan"] is not None
    assert c["_plan_step_index"] == -1


def test_reflection_failure_retry():
    host = MagicMock()
    host._planner.generate_plan.return_value = Plan(goal="", steps=[], plan_confidence=0.0)
    host._tool_registry.list_tools.return_value = []
    host._helper._load_checkpoint.return_value = None
    host._planner.plan.return_value = {"step": -1, "action": "plan"}
    host._verifier.verify.return_value = True
    host._tool_exec._reflect_before_tool.return_value = {}
    host._core_tools._check_budget.return_value = True
    host._core_tools._accumulate_cost.return_value = None
    host._loop_detector.record.return_value = None
    host._loop_detector.detect.return_value = None
    engine = ExecutionEngine(host)
    spec = {"max_permission": "read", "default_temperature": 0.7}
    tool_result = {"success": True, "data": "bad data"}
    decision = MagicMock()
    decision.reasoning = "test call"
    v_result = VerificationResult(
        passed=False,
        checks=[CheckResult(name="layer1_filter", passed=False, detail="高风险内容")],
        confidence=0.0,
    )
    host._verifier.verify_step.return_value = v_result
    c = {
        "goal": "test",
        "agent_key": "test_agent",
        "context": {},
        "messages": [{"role": "system", "content": "test"}],
        "logs": [],
        "tool_calls": 0,
        "_plan": None,
        "_plan_step_index": -1,
    }
    host._tool_registry.call.return_value = tool_result
    result = engine._process_tool_call(c, 0, "test_tool", {}, decision, {}, 100, spec)
    assert result is None
    assert c["_reflection_retries"] == 1
    assert any("反思反馈" in m.get("content", "") for m in c["messages"])
    assert any(log.get("type") == "reflection_failure" for log in c["logs"])


def test_reflection_pass():
    host = MagicMock()
    host._planner.generate_plan.return_value = Plan(goal="", steps=[], plan_confidence=0.0)
    host._tool_registry.list_tools.return_value = []
    host._helper._load_checkpoint.return_value = None
    host._planner.plan.return_value = {"step": -1, "action": "plan"}
    host._verifier.verify.return_value = True
    host._tool_exec._reflect_before_tool.return_value = {}
    host._core_tools._check_budget.return_value = True
    host._core_tools._accumulate_cost.return_value = None
    host._loop_detector.record.return_value = None
    host._loop_detector.detect.return_value = None
    host._tool_exec._save_step_checkpoint.return_value = None
    engine = ExecutionEngine(host)
    spec = {"max_permission": "read", "default_temperature": 0.7}
    tool_result = {"success": True, "data": "good data"}
    decision = MagicMock()
    decision.reasoning = "test call"
    decision.model_dump.return_value = {"action": "call_tool", "tool": "test_tool", "params": {}}
    v_result = VerificationResult(
        passed=True,
        checks=[
            CheckResult(name="assertions", passed=True, detail="All assertions passed"),
            CheckResult(name="layer1_filter", passed=True, detail="Layer1 passed"),
            CheckResult(name="llm_verification", passed=True, detail="llm验证通过"),
        ],
        confidence=1.0,
    )
    host._verifier.verify_step.return_value = v_result
    host._tool_registry.call.return_value = tool_result
    c = {
        "goal": "test",
        "agent_key": "test_agent",
        "context": {},
        "messages": [{"role": "system", "content": "test"}],
        "logs": [],
        "tool_calls": 0,
        "_plan": None,
        "_plan_step_index": -1,
    }
    result = engine._process_tool_call(c, 0, "test_tool", {}, decision, {}, 100, spec)
    assert result is None
    assert any("已通过验证" in m.get("content", "") for m in c["messages"])
