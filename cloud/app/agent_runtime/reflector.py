"""L4 Meta-Cognitive: Reflector — adjusts, replaces, or replans based on severity."""

import json
import logging

from pydantic import BaseModel

from cloud.app.agent_runtime.analyzer import Analysis
from cloud.app.agent_runtime.planner import Plan, PlanGenerator, PlanStep
from cloud.app.agent_runtime.verifier import SafetyGuard

logger = logging.getLogger(__name__)


class ReflectionResult(BaseModel):
    plan: Plan | None = None
    action: str = ""  # adjust_params | replace_step | replan | cannot_fix
    detail: str = ""


class Reflector:
    """Reflects on failed steps and produces adjusted plans.

    Low severity  → adjust_params (modify current step params)
    Medium severity → replace_step (use fallback)
    High severity  → replan (generate entirely new plan)
    If cannot fix  → return None (triggers escalation protocol)
    """

    def __init__(self, plan_generator: PlanGenerator | None = None, llm_url: str = "http://localhost:8000/ai/chat"):
        self._plan_generator = plan_generator or PlanGenerator(llm_url=llm_url)
        self._llm_url = llm_url
        self._max_reflections = 3
        self._guard = SafetyGuard()

    def review_decision(
        self,
        task: str,
        decision,
        context: dict | None = None,
        level: str = "balanced",
    ) -> ReflectionResult:
        """Pre-tool reflection after LLM decision generation.

        light: compliance-only static check.
        balanced: compliance, safety, and cost static checks.
        thorough: full context LLM review, optionally adjusting tool params.
        """
        ctx = context or {}
        decision_data = decision.model_dump() if hasattr(decision, "model_dump") else dict(decision)
        action = decision_data.get("action", "")
        tool = decision_data.get("tool") or ""
        params = decision_data.get("params") or {}

        if action != "call_tool":
            return ReflectionResult(plan=None, action="pass", detail=f"{level}: no tool execution")

        if level == "light":
            return self._light_review(tool, params)

        if level == "thorough":
            return self._thorough_review(task, tool, params, decision_data, ctx)

        return self._balanced_review(tool, params, ctx)

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

    def _light_review(self, tool: str, params: dict) -> ReflectionResult:
        violations = self._compliance_violations(tool, params)
        if violations:
            return ReflectionResult(plan=None, action="cannot_fix", detail=f"light compliance warning: {violations}")
        return ReflectionResult(plan=None, action="pass", detail="light compliance passed")

    def _balanced_review(self, tool: str, params: dict, context: dict) -> ReflectionResult:
        violations = self._compliance_violations(tool, params)
        safety = self._guard.check_params(tool, params)
        cost = context.get("cost") or {}
        total_cost = float(cost.get("total_cost", 0.0) or 0.0)
        max_cost = cost.get("max_cost")
        cost_ok = max_cost is None or total_cost <= float(max_cost)

        issues = []
        if violations:
            issues.append(f"compliance={violations}")
        if not safety.passed:
            issues.append(f"safety={safety.detail}")
        if not cost_ok:
            issues.append(f"cost={total_cost}>{max_cost}")

        if issues:
            return ReflectionResult(plan=None, action="cannot_fix", detail="balanced warning: " + "; ".join(issues))
        return ReflectionResult(plan=None, action="pass", detail="balanced compliance/safety/cost passed")

    def _thorough_review(self, task: str, tool: str, params: dict, decision: dict, context: dict) -> ReflectionResult:
        prompt = (
            "Review this planned tool call before execution.\n"
            f"Task: {task}\n"
            f"Decision: {json.dumps(decision, ensure_ascii=False)}\n"
            f"Context: {json.dumps(context, ensure_ascii=False)}\n\n"
            "Check compliance, safety, cost, context fit, and tool/parameter correctness. "
            'Reply ONLY JSON: {"action": "pass"|"adjust_params"|"cannot_fix", '
            '"params": {...}, "detail": "..."}'
        )
        reply = self._cheap_llm([{"role": "user", "content": prompt}])
        parsed = self._extract_json(reply)
        action = parsed.get("action", "pass")
        detail = parsed.get("detail", "")
        if action == "adjust_params":
            adjusted = parsed.get("params") or params
            plan = Plan(
                goal=task,
                steps=[
                    PlanStep(
                        step_id="pre_tool_reflection",
                        description="Reflector adjusted tool parameters before execution",
                        tool=tool,
                        params_template=adjusted,
                    )
                ],
                max_steps=1,
                plan_confidence=0.8,
            )
            return ReflectionResult(plan=plan, action="adjust_params", detail=detail or "thorough adjusted params")
        if action == "cannot_fix":
            return ReflectionResult(plan=None, action="cannot_fix", detail=detail or "thorough warning")
        return ReflectionResult(plan=None, action="pass", detail=detail or "thorough passed")

    @staticmethod
    def _compliance_violations(tool: str, params: dict) -> list[str]:
        raw = json.dumps({"tool": tool, "params": params}, ensure_ascii=False).lower()
        blocked_terms = {
            "rebate",
            "kickback",
            "bribe",
            "统方",
            "回扣",
            "贿赂",
            "利益输送",
            "违规",
        }
        return sorted(term for term in blocked_terms if term in raw)

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
        """Use a cheaper/faster model for reflection (lower temp, fewer tokens)."""
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
