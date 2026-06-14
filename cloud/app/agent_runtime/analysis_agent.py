"""AnalysisAgent — wraps the analyzer pipeline with CostGovernor budget enforcement."""

import logging
from typing import Any

from cloud.app.agent_runtime.analyzer.hypothesis import HypothesisEngine
from cloud.app.agent_runtime.cost_governor import CostGovernor

logger = logging.getLogger(__name__)

MAX_TOKENS_PER_STEP = 500


class AnalysisAgent:
    """Anomaly root-cause analysis agent with cost-governed execution.

    Wraps the hypothesis pipeline (generate → plan → verify → evaluate → rank)
    with CostGovernor budget checks before each tool call.
    """

    def __init__(self, cost_governor: CostGovernor | None = None, hypothesis_engine: HypothesisEngine | None = None):
        self._governor = cost_governor or CostGovernor(max_cost=0.50)
        self._engine = hypothesis_engine or HypothesisEngine()

    def execute(self, red_light_event: dict) -> dict[str, Any]:
        """Execute the full analysis pipeline under cost governance.

        Before each major step, checks whether the budget allows continued execution.
        If budget is exceeded, returns partial results instead of crashing.

        Args:
            red_light_event: Compliance red-light event dict to analyze.

        Returns:
            dict with keys: status ("completed" or "budget_exceeded"),
                            partial_result (if budget exceeded),
                            hypotheses (ranked list),
                            narrative (RootCauseNarrative if available).
        """
        if not self._governor.check("analysis_agent", 0, MAX_TOKENS_PER_STEP):
            return self._budget_exceeded_response("hypothesis_generation", [])

        logger.info("AnalysisAgent executing for event: %s", red_light_event.get("event_id", "unknown"))

        hypotheses = self._engine.generate_hypotheses(red_light_event)
        self._record_step(100, 200)

        if not self._governor.check("analysis_agent", 0, MAX_TOKENS_PER_STEP):
            return self._budget_exceeded_response("evidence_collection", hypotheses)

        all_results = []
        for hyp in hypotheses:
            if not self._governor.check("analysis_agent", 0, MAX_TOKENS_PER_STEP):
                break
            plan = self._engine.design_verification_plan(hyp)
            data = self._engine.execute_verification(plan)
            results = self._engine.evaluate_hypotheses([hyp], data)
            all_results.extend(results)
            self._record_step(50, 100)

        if not self._governor.check("analysis_agent", 0, MAX_TOKENS_PER_STEP):
            return self._budget_exceeded_response("ranking", hypotheses, all_results)

        ranked = self._engine.rank_hypotheses(hypotheses, all_results)
        self._record_step(50, 50)

        narrative = self._engine.generate_narrative(hypotheses, all_results)

        return {
            "status": "completed",
            "hypotheses": [h.model_dump() for h in ranked],
            "narrative": narrative,
        }

    def _record_step(self, input_tokens: int, output_tokens: int) -> None:
        self._governor.record("analysis_agent", input_tokens, output_tokens, "cloud_agent")

    def _budget_exceeded_response(
        self,
        step: str,
        hypotheses: list | None = None,
        results: list | None = None,
    ) -> dict[str, Any]:
        """Build a partial result when budget is exceeded."""
        ranked = self._engine.rank_hypotheses(hypotheses or [], results)
        narrative = None
        if results:
            narrative = self._engine.generate_narrative(hypotheses or [], results)
        return {
            "status": "budget_exceeded",
            "partial_result": {
                "last_step": step,
                "hypotheses": [h.model_dump() for h in ranked],
                "narrative": narrative,
            },
        }
