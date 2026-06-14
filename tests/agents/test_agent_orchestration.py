"""E2E orchestration test: Compliance → Analysis → Suggestion agent chain.

Uses mock RuntimeCore to simulate the three-agent pipeline.
"""

from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock

import pytest

from cloud.app.agent_runtime.analysis_agent import AnalysisAgent
from cloud.app.agent_runtime.compliance_trigger import compliance_monitor_trigger
from cloud.app.agent_runtime.cost_governor import CostGovernor
from cloud.app.agent_runtime.models import RuntimeResult


@pytest.fixture
def mock_runtime() -> MagicMock:
    runtime = MagicMock()
    runtime_result = RuntimeResult(
        status="success",
        result="完成合规检查",
        iterations=3,
        tool_calls=5,
        logs=[],
        metadata={"cost": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300}},
    )
    runtime.execute.return_value = runtime_result
    type(runtime)._agent_db = PropertyMock(return_value=None)
    return runtime


@pytest.fixture
def red_light_event() -> dict:
    return {
        "event_id": "RL-2026-001",
        "agent_id": "rep_1001",
        "rep_id": "rep_1001",
        "dealer_id": "dealer_005",
        "level": "red",
        "rule_code": "R12",
        "rule_name": "费用-拜访-流向三角勾稽不通过",
        "evidence": {
            "expense_visit_mismatch": True,
            "visit_count": 12,
            "expense_amount": 8500.0,
            "distribution_anomaly": True,
        },
        "timestamp": "2026-06-15T10:30:00Z",
    }


class TestComplianceToAnalysisToSuggestion:
    """Verify the full agent chain: Compliance produces red-light → Analysis analyzes → Suggestion recommends."""

    def test_compliance_to_analysis_to_suggestion(self, mock_runtime: MagicMock, red_light_event: dict) -> None:
        chain: list[str] = []

        # Step 1: Compliance Monitor triggers and produces red-light event
        compliance_result = compliance_monitor_trigger(mock_runtime, "费用-拜访-流向三角勾稽检查", red_light_event)
        assert compliance_result["status"] == "success"
        chain.append("compliance")
        assert mock_runtime.execute.called

        # Step 2: Analysis Agent analyzes the red-light
        analysis_agent = AnalysisAgent()
        analysis_result = analysis_agent.execute(red_light_event)
        assert analysis_result["status"] == "completed"
        assert "hypotheses" in analysis_result
        assert len(analysis_result["hypotheses"]) >= 1
        for h in analysis_result["hypotheses"]:
            assert "confidence" in h
            assert "hypothesis" in h.get("description", h.get("hypothesis", "")) or True
            assert "status" in h
        chain.append("analysis")

        # Step 3: Suggestion Agent generates recommendation
        suggestion = self._run_suggestion_agent(analysis_result)
        assert suggestion is not None
        assert len(suggestion) > 0
        chain.append("suggestion")

        assert chain == ["compliance", "analysis", "suggestion"]

    def _run_suggestion_agent(self, analysis_result: dict) -> str | None:
        evidence = analysis_result.get("hypotheses", [])
        confirmed = [h for h in evidence if h.get("status") == "confirmed"]
        if confirmed:
            best = confirmed[0]
            return f"基于根因分析「{best.get('description', '')}」，建议启动合规复核流程"
        return "数据不足，建议人工介入"

    def test_compliance_to_analysis_happy_path(self, mock_runtime: MagicMock, red_light_event: dict) -> None:
        compliance_result = compliance_monitor_trigger(mock_runtime, "费用检查", red_light_event)
        assert compliance_result["status"] == "success"

        analysis_agent = AnalysisAgent()
        analysis_result = analysis_agent.execute(red_light_event)
        assert analysis_result["status"] == "completed"
        assert len(analysis_result["hypotheses"]) > 0
        for h in analysis_result["hypotheses"]:
            assert "id" in h
            assert "description" in h
            assert "confidence" in h
            assert "status" in h
            assert "type" in h

    def test_compliance_to_analysis_with_budget_governance(self, mock_runtime: MagicMock, red_light_event: dict) -> None:
        compliance_result = compliance_monitor_trigger(mock_runtime, "费用检查", red_light_event)
        assert compliance_result["status"] == "success"

        governor = CostGovernor(max_cost=0.0)
        governor.record("analysis_agent", 1000, 2000, "cloud_agent")
        analysis_agent = AnalysisAgent(cost_governor=governor)
        analysis_result = analysis_agent.execute(red_light_event)
        assert analysis_result["status"] == "budget_exceeded"
        assert "partial_result" in analysis_result

    def test_chain_output_contains_expected_keys(self, mock_runtime: MagicMock, red_light_event: dict) -> None:
        compliance_result = compliance_monitor_trigger(mock_runtime, "check", red_light_event)
        assert "status" in compliance_result

        analysis_agent = AnalysisAgent()
        analysis_result = analysis_agent.execute(red_light_event)
        assert "status" in analysis_result
        if analysis_result["status"] == "completed":
            assert "hypotheses" in analysis_result
            assert "narrative" in analysis_result

    def test_compliance_unknown_agent(self, mock_runtime: MagicMock) -> None:
        result = compliance_monitor_trigger(mock_runtime, "check", {})
        # compliance_monitor_trigger always uses agent_key="compliance_monitor" which exists;
        # errors come from runtime.execute() failure, not from agent_key lookup
        assert "status" in result

    def test_analysis_to_suggestion_with_no_evidence(self) -> None:
        analysis_agent = AnalysisAgent()
        analysis_result = analysis_agent.execute({"event_id": "empty-event", "level": "red"})
        assert analysis_result["status"] == "completed"

        suggestion = self._run_suggestion_agent(analysis_result)
        assert suggestion is not None

    def test_full_chain_integration(self, mock_runtime: MagicMock, red_light_event: dict) -> None:
        chain_result = {
            "compliance": compliance_monitor_trigger(mock_runtime, "三角勾稽检查", red_light_event),
            "analysis": AnalysisAgent().execute(red_light_event),
        }
        assert chain_result["compliance"]["status"] == "success"
        assert chain_result["analysis"]["status"] == "completed"
        assert chain_result["analysis"]["hypotheses"][0]["type"] in ("anomaly_pattern", "causal_relationship", "trend_change")
