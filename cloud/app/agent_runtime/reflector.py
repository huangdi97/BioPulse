"""L4 Meta-Cognitive: Reflector — adjusts, replaces, or replans based on severity."""

import json
import logging

from cloud.app.agent_runtime.analyzer import Analysis
from cloud.app.agent_runtime.planner import Plan, Planner
from cloud.app.agent_runtime.reflection_analyzer import ReflectionAnalyzer, ReflectionResult
from cloud.app.agent_runtime.safety_guard import SafetyGuard
from shared.config import settings as config_settings

logger = logging.getLogger(__name__)


class Reflector:
    """Reflects on failed steps and produces adjusted plans."""

    def __init__(self, plan_generator: Planner | None = None, llm_url: str = config_settings.ai_chat_url):
        self._plan_generator = plan_generator or Planner(llm_url=llm_url)
        self._llm_url = llm_url
        self._max_reflections = 3
        self._guard = SafetyGuard()
        self._analyzer = ReflectionAnalyzer(llm_url=llm_url, guard=self._guard)

    def review_decision(
        self,
        task: str,
        decision,
        context: dict | None = None,
        level: str = "balanced",
    ) -> ReflectionResult:
        """Pre-tool reflection after LLM decision generation."""
        return self._analyzer.review_decision(task, decision, context, level)

    def reflect(
        self,
        task: str,
        original_plan: Plan,
        analysis: Analysis,
        context: dict | None = None,
    ) -> ReflectionResult:
        """Main reflection entry — dispatches by severity."""
        ctx = context or {}

        if analysis.severity == "low":
            return self._adjust_params(task, original_plan, analysis, ctx)
        if analysis.severity == "medium":
            return self._replace_step(task, original_plan, analysis, ctx)
        if analysis.severity == "high":
            return self._replan(task, original_plan, analysis, ctx)

        return ReflectionResult(plan=None, action="cannot_fix", detail=f"Unknown severity: {analysis.severity}")

    def _adjust_params(self, task: str, plan: Plan, analysis: Analysis, context: dict) -> ReflectionResult:
        """Low severity: modify params of the failed step using a cheap LLM call."""
        if not plan.steps:
            return ReflectionResult(plan=None, action="cannot_fix", detail="No steps to adjust")

        failed_step = plan.steps[-1] if plan.steps else plan.steps[0]
        prompt = (
            f"Task: {task}\nFailed step: {failed_step.step_id} ({failed_step.tool})\n"
            f"Current params: {json.dumps(failed_step.params_template)}\n"
            f"Issue: {analysis.cause} — {analysis.suggestion}\n"
            f"Context: {json.dumps(context, ensure_ascii=False)}\n\n"
            "Output ONLY a JSON dict with adjusted params for this step."
        )
        try:
            reply = self._cheap_llm([{"role": "user", "content": prompt}])
            adjusted_params = self._extract_json(reply)
            failed_step.params_template = adjusted_params
            return ReflectionResult(
                plan=plan,
                action="adjust_params",
                detail=f"Adjusted params for {failed_step.step_id}: {json.dumps(adjusted_params)}",
            )
        except Exception as e:
            logger.error("Param adjustment failed: %s", e)
            return ReflectionResult(plan=None, action="cannot_fix", detail=f"Adjustment error: {e}")

    def _replace_step(self, task: str, plan: Plan, analysis: Analysis, context: dict) -> ReflectionResult:
        """Medium severity: find and use a fallback for the failed step."""
        if not plan.steps:
            return ReflectionResult(plan=None, action="cannot_fix", detail="No steps to replace")

        for i, step in enumerate(plan.steps):
            if step.fallback:
                prompt = (
                    f"Replace step '{step.step_id}' (tool: {step.tool}) with its fallback '{step.fallback}'.\n"
                    f"Task: {task}\nIssue: {analysis.cause}\n"
                    f"Context: {json.dumps(context, ensure_ascii=False)}\n\n"
                    'Output ONLY a JSON: {"tool": "fallback_tool", "params": {...}}'
                )
                try:
                    reply = self._cheap_llm([{"role": "user", "content": prompt}])
                    replacement = self._extract_json(reply)
                    plan.steps[i].tool = replacement.get("tool", step.fallback)
                    plan.steps[i].params_template = replacement.get("params", {})
                    return ReflectionResult(
                        plan=plan,
                        action="replace_step",
                        detail=f"Replaced {step.step_id} with fallback: {plan.steps[i].tool}",
                    )
                except Exception as e:
                    logger.error("Step replacement failed: %s", e)

        return ReflectionResult(plan=None, action="cannot_fix", detail="No fallback available for failed step")

    def _replan(self, task: str, original_plan: Plan, analysis: Analysis, context: dict) -> ReflectionResult:
        """High severity: generate an entirely new plan with different strategy."""
        try:
            tools_used = {s.tool for s in original_plan.steps}
            new_plan = self._plan_generator.generate_plan(
                goal=original_plan.goal,
                tools=list(tools_used),
                context={**context, "_previous_failure": analysis.cause, "_previous_plan": original_plan.goal},
            )
            if new_plan.steps:
                return ReflectionResult(
                    plan=new_plan,
                    action="replan",
                    detail=f"Generated new {len(new_plan.steps)}-step plan after {analysis.cause}",
                )
            return ReflectionResult(plan=None, action="cannot_fix", detail="Replanning produced empty plan")
        except Exception as e:
            logger.error("Replanning failed: %s", e)
            return ReflectionResult(plan=None, action="cannot_fix", detail=f"Replan error: {e}")

    def _cheap_llm(self, messages: list[dict]) -> str:
        import urllib.request

        body = json.dumps({"messages": messages, "temperature": 0.1, "max_tokens": 1024}).encode("utf-8")
        req = urllib.request.Request(
            self._llm_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as rp:
            data = json.loads(rp.read().decode("utf-8"))
        return data.get("data", {}).get("reply", "")

    @staticmethod
    def _extract_json(raw: str) -> dict:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            raw = raw.rsplit("```", 1)[0]
        return json.loads(raw)
