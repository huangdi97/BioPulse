"""Decision analysis — compliance, safety, cost & thorough LLM review."""

import json
import logging

from pydantic import BaseModel

from cloud.app.agent_runtime.planner import Plan, PlanStep
from cloud.app.agent_runtime.safety_guard import SafetyGuard
from shared.config import settings as config_settings

logger = logging.getLogger(__name__)


class ReflectionResult(BaseModel):
    plan: Plan | None = None
    action: str = ""
    detail: str = ""


class ReflectionAnalyzer:
    """Analyzes tool decisions for compliance, safety, cost, and context fit."""

    def __init__(self, llm_url: str = config_settings.ai_chat_url, guard: SafetyGuard | None = None):
        self._llm_url = llm_url
        self._guard = guard or SafetyGuard()

    def review_decision(
        self,
        task: str,
        decision,
        context: dict | None = None,
        level: str = "balanced",
    ) -> ReflectionResult:
        """review decision."""
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
