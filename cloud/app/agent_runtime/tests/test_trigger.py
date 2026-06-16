"""Tests for generic agent trigger (run_agent_trigger)."""

from unittest.mock import MagicMock

from cloud.app.agent_runtime.models import RuntimeResult
from cloud.app.agent_runtime.trigger import run_agent_trigger


def _mock_runtime() -> MagicMock:
    runtime = MagicMock()
    runtime.execute.return_value = RuntimeResult(
        status="success",
        result="done",
        iterations=2,
        tool_calls=3,
        logs=[],
        metadata={},
    )
    return runtime


def test_run_agent_trigger_success():
    """test run agent trigger success."""
    runtime = _mock_runtime()
    result = run_agent_trigger(runtime, "anomaly_analysis", "分析红灯事件", {"event_id": "E1"})
    assert result["status"] == "success"
    assert result["result"] == "done"
    assert result["elapsed_seconds"] >= 0


def test_run_agent_trigger_unknown_agent():
    """test run agent trigger unknown agent."""
    runtime = _mock_runtime()
    result = run_agent_trigger(runtime, "nonexistent", "task", {"event_id": "E1"})
    assert result["status"] == "error"
    assert "unknown agent" in result["result"]


def test_run_agent_trigger_with_context_extras():
    """test run agent trigger with context extras."""
    runtime = _mock_runtime()
    result = run_agent_trigger(runtime, "compliance_monitor", "合规检查", {"rep_id": "R1"}, {"_plan": [{"step": 1}]})
    assert result["status"] == "success"


def test_run_agent_trigger_without_event():
    """test run agent trigger without event."""
    runtime = _mock_runtime()
    result = run_agent_trigger(runtime, "sales_suggestion", "生成拜访后销售策略建议")
    assert result["status"] == "success"
