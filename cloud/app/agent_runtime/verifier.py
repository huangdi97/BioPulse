"""L4 Meta-Cognitive: Verifier — three-layer result verification (assertion, rule, LLM)."""

import json
import logging

from pydantic import BaseModel

from cloud.app.agent_runtime.planner import Plan, PlanStep

logger = logging.getLogger(__name__)


class CheckResult(BaseModel):
    name: str
    passed: bool
    detail: str = ""


class VerificationResult(BaseModel):
    passed: bool = False
    checks: list[CheckResult] = []
    confidence: float = 0.0


class SafetyGuard:
    """Parameter boundary check and side-effect prediction."""

    @staticmethod
    def check_params(tool: str, params: dict) -> CheckResult:
        risky_keys = {"password", "secret", "token", "key", "certificate", "private"}
        violations = [k for k in params if any(r in k.lower() for r in risky_keys)]
        return CheckResult(
            name="param_boundary",
            passed=len(violations) == 0,
            detail=f"Risky params: {violations}" if violations else "All params safe",
        )

    @staticmethod
    def predict_side_effect(tool: str, params: dict) -> CheckResult:
        write_tools = {"create_notification", "write_memory", "compliance_check", "agent_brain_set"}
        is_write = tool in write_tools
        return CheckResult(
            name="side_effect",
            passed=True,
            detail=f"Write operation: {tool}" if is_write else "Read-only operation",
        )


class Verifier:
    """Three-layer verification: assertions, rule matching, LLM."""

    def __init__(self, llm_url: str = "http://localhost:8000/ai/chat"):
        self._llm_url = llm_url
        self._guard = SafetyGuard()

    def verify_step(self, step: PlanStep, result: dict) -> VerificationResult:
        """Run all three verification layers on a single step result."""
        checks: list[CheckResult] = []

        # Layer 1: Python assertions (free)
        checks.append(self._layer1_assertions(step, result))

        # Layer 2: Rule matching (free)
        checks.append(self._guard.check_params(step.tool, step.params_template))
        checks.append(self._guard.predict_side_effect(step.tool, result))

        # Layer 3: LLM verification (costly, on demand)
        if not all(c.passed for c in checks):
            llm_check = self._layer3_llm(step, result)
            checks.append(llm_check)
        else:
            checks.append(CheckResult(name="llm_verification", passed=True, detail="Skipped — lower layers passed"))

        passed = all(c.passed for c in checks)
        confidence = sum(1.0 for c in checks if c.passed) / max(len(checks), 1)
        return VerificationResult(passed=passed, checks=checks, confidence=confidence)

    def verify_global(self, plan: Plan, results: list[dict]) -> bool:
        """Verify overall plan completion against completion_conditions."""
        if not plan.completion_conditions:
            return True
        prompt = (
            f"Plan goal: {plan.goal}\n"
            f"Completion conditions: {json.dumps(plan.completion_conditions)}\n"
            f"Step results: {json.dumps(results, ensure_ascii=False)}\n\n"
            "Are all completion conditions satisfied? Reply ONLY 'true' or 'false'."
        )
        try:
            reply = self._call_llm([{"role": "user", "content": prompt}])
            return reply.strip().lower() == "true"
        except Exception as e:
            logger.error("Global verification failed: %s", e)
            return False

    @staticmethod
    def _layer1_assertions(step: PlanStep, result: dict) -> CheckResult:
        """Basic Python-level assertions on the result."""
        details = []
        if result is None:
            return CheckResult(name="assertions", passed=False, detail="Result is None")

        success = result.get("success", False)
        if not success:
            details.append(f"Result success=False: {result.get('error', 'no error')}")

        if details:
            return CheckResult(name="assertions", passed=False, detail="; ".join(details))
        return CheckResult(name="assertions", passed=True, detail="All assertions passed")

    def _layer3_llm(self, step: PlanStep, result: dict) -> CheckResult:
        """LLM-based semantic verification of step result."""
        prompt = (
            f"Verify the following step result:\n"
            f"Step: {step.description} (tool: {step.tool})\n"
            f"Verification criteria: {json.dumps(step.verification_criteria)}\n"
            f"Result: {json.dumps(result, ensure_ascii=False)}\n\n"
            'Reply ONLY a JSON: {"passed": bool, "reason": "..."}'
        )
        try:
            reply = self._call_llm([{"role": "user", "content": prompt}])
            parsed = self._extract_json(reply)
            return CheckResult(
                name="llm_verification",
                passed=parsed.get("passed", False),
                detail=parsed.get("reason", "No reason given"),
            )
        except Exception as e:
            return CheckResult(name="llm_verification", passed=False, detail=f"LLM error: {e}")

    def _call_llm(self, messages: list[dict]) -> str:
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
