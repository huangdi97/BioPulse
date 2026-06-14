"""AnalysisAgent 单元测试 — hypothesis pipeline + cost governance."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from cloud.app.agent_runtime.analysis_agent import AnalysisAgent
from cloud.app.agent_runtime.analyzer.hypothesis import HypothesisEngine
from cloud.app.agent_runtime.analyzer.models import Hypothesis, RootCauseNarrative, VerificationPlan, VerificationResult
from cloud.app.agent_runtime.cost_governor import CostGovernor


@pytest.fixture
def sample_event() -> dict:
    return {
        "event_id": "RL-TEST-001",
        "agent_id": "rep_42",
        "rep_id": "rep_42",
        "level": "red",
        "rule_code": "R07",
        "rule_name": "费用虚增规则",
        "evidence": {
            "expense_visit_mismatch": True,
            "visit_count": 15,
            "expense_amount": 12000.0,
        },
        "timestamp": "2026-06-15T14:00:00Z",
    }


@pytest.fixture
def empty_event() -> dict:
    return {}


class TestHypothesisGeneration:
    """T4.1 — hypothesis generation (normal input)."""

    def test_generate_hypotheses_normal_input(self, sample_event: dict) -> None:
        engine = HypothesisEngine()
        hypotheses = engine.generate_hypotheses(sample_event)
        assert len(hypotheses) >= 2
        for h in hypotheses:
            assert isinstance(h, Hypothesis)
            assert h.id
            assert h.description
            assert 0.0 <= h.confidence <= 1.0
            assert h.status == "pending"
            assert h.type in ("anomaly_pattern", "causal_relationship", "trend_change")

    def test_generate_hypotheses_llm_fallback(self, sample_event: dict) -> None:
        engine = HypothesisEngine()
        with patch.object(engine, "_default_hypotheses", wraps=engine._default_hypotheses) as mock_default:
            with patch("cloud.app.agent_runtime.analyzer.hypothesis.call_llm", side_effect=Exception("LLM down")):
                hypotheses = engine.generate_hypotheses(sample_event)
                assert len(hypotheses) == 3
                mock_default.assert_called_once()


class TestHypothesisRanking:
    """T4.2 — hypothesis ranking (multiple hypotheses sorting)."""

    def test_rank_hypotheses_by_confidence(self) -> None:
        engine = HypothesisEngine()
        h1 = Hypothesis(id="h1", description="低置信度", confidence=0.3, status="pending")
        h2 = Hypothesis(id="h2", description="中置信度", confidence=0.6, status="pending")
        h3 = Hypothesis(id="h3", description="高置信度", confidence=0.9, status="pending")
        ranked = engine.rank_hypotheses([h1, h2, h3])
        assert ranked[0].id == "h3"
        assert ranked[1].id == "h2"
        assert ranked[2].id == "h1"

    def test_rank_hypotheses_with_validation_results(self) -> None:
        engine = HypothesisEngine()
        h1 = Hypothesis(id="h1", description="hyp A", confidence=0.3, status="pending")
        h2 = Hypothesis(id="h2", description="hyp B", confidence=0.6, status="pending")
        r1 = VerificationResult(hypothesis_id="h1", confirmed=True, confidence=0.85, evidence=["ev1"], narrative="confirmed")
        r2 = VerificationResult(hypothesis_id="h2", confirmed=False, confidence=0.25, evidence=["ev2"], narrative="falsified")
        ranked = engine.rank_hypotheses([h1, h2], [r1, r2])
        assert ranked[0].id == "h1"
        assert ranked[0].confidence == 0.85
        assert ranked[0].status == "confirmed"
        assert ranked[1].id == "h2"
        assert ranked[1].confidence == 0.25
        assert ranked[1].status == "falsified"


class TestEvidenceCollection:
    """T4.3 — evidence collection success."""

    def test_execute_verification_success(self) -> None:
        engine = HypothesisEngine()
        plan = VerificationPlan(
            hypothesis_id="h1",
            checks=[
                {"check": "拜访量趋势分析", "data_needed": ["visit_count_by_rep", "visit_duration"]},
            ],
        )
        result = engine.execute_verification(plan)
        assert "拜访量趋势分析" in result
        assert result["拜访量趋势分析"]["status"] == "executed"
        assert "visit_count_by_rep" in result["拜访量趋势分析"]["data"]

    def test_execute_verification_empty_plan(self) -> None:
        engine = HypothesisEngine()
        plan = VerificationPlan(hypothesis_id="h1", checks=[])
        result = engine.execute_verification(plan)
        assert result == {}

    """T4.4 — evidence collection failure (empty result)."""

    def test_execute_verification_empty_check(self) -> None:
        engine = HypothesisEngine()
        plan = VerificationPlan(hypothesis_id="h1", checks=[{"check": "空检查", "data_needed": []}])
        result = engine.execute_verification(plan)
        assert "空检查" in result
        assert result["空检查"]["data"] == {}


class TestValidation:
    """T4.5 — validation pass."""

    def test_evaluate_confirmed_hypothesis(self) -> None:
        engine = HypothesisEngine()
        h = Hypothesis(id="h1", description="拜访数据可能存在虚增", confidence=0.5, status="pending")
        results = engine.evaluate_hypotheses([h], {})
        assert len(results) == 1
        assert results[0].confirmed is True
        assert results[0].confidence >= 0.5

    """T4.6 — validation fail."""

    def test_evaluate_falsified_hypothesis(self) -> None:
        engine = HypothesisEngine()
        h = Hypothesis(id="h2", description="普通业务波动", confidence=0.3, status="pending")
        results = engine.evaluate_hypotheses([h], {})
        assert len(results) == 1
        assert results[0].confirmed is False
        assert h.status == "falsified"


class TestCostControl:
    """T4.7 — cost control: normal budget."""

    def test_execute_with_normal_budget(self, sample_event: dict) -> None:
        agent = AnalysisAgent()
        result = agent.execute(sample_event)
        assert result["status"] == "completed"
        assert len(result["hypotheses"]) >= 2

    """T4.8 — cost control: budget exceeded."""

    def test_execute_with_budget_exceeded(self, sample_event: dict) -> None:
        governor = CostGovernor(max_cost=0.0)
        governor.record("test", 10000, 50000, "cloud_agent")
        agent = AnalysisAgent(cost_governor=governor)
        result = agent.execute(sample_event)
        assert result["status"] == "budget_exceeded"
        assert "partial_result" in result
        partial = result["partial_result"]
        assert "last_step" in partial
        assert "hypotheses" in partial

    def test_execute_budget_exceeded_mid_pipeline(self, sample_event: dict) -> None:
        governor = CostGovernor(max_cost=0.001)
        agent = AnalysisAgent(cost_governor=governor)
        result = agent.execute(sample_event)
        assert result["status"] in ("completed", "budget_exceeded")
        if result["status"] == "budget_exceeded":
            assert "partial_result" in result


class TestEdgeCases:
    """T4.9 — empty data input."""

    def test_execute_empty_event(self) -> None:
        agent = AnalysisAgent()
        result = agent.execute({})
        assert result["status"] == "completed"
        assert len(result["hypotheses"]) >= 1

    """T4.10 — boundary: iteration count (loop convergence)."""

    def test_hypothesis_verification_loop_multiple_hypotheses(self, sample_event: dict) -> None:
        engine = HypothesisEngine()
        output = engine.hypothesis_verification_loop(sample_event)
        assert output["status"] == "completed"
        assert len(output["hypotheses"]) >= 2
        assert isinstance(output["narrative"], RootCauseNarrative)


class TestDesignVerificationPlan:
    def test_design_plan_for_trend_hypothesis(self) -> None:
        engine = HypothesisEngine()
        h = Hypothesis(id="h3", description="近期费用趋势异常上升", confidence=0.5, status="pending", type="trend_change")
        plan = engine.design_verification_plan(h)
        check_names = [c["check"] for c in plan.checks]
        assert "时间序列趋势分析" in check_names

    def test_design_plan_fallback_generic(self) -> None:
        engine = HypothesisEngine()
        h = Hypothesis(id="h4", description="随机异常", confidence=0.3, status="pending")
        plan = engine.design_verification_plan(h)
        check_names = [c["check"] for c in plan.checks]
        assert "通用数据交叉验证" in check_names
