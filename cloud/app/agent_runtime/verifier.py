"""L4 Meta-Cognitive: Verifier — three-layer result verification (assertion, rule, LLM)."""

import json
import logging
import urllib.request

from pydantic import BaseModel

from cloud.app.agent_runtime.guard import GuardLayer1
from cloud.app.agent_runtime.planner import Plan, PlanStep
from shared.config import settings as config_settings

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


class RuleEngineLLM:
    """LLM rule checker with static SafetyGuard fallback."""

    DEFAULT_RULES = [
        {
            "id": "param_boundary",
            "description": "Tool parameters must not expose passwords, secrets, tokens, keys, certificates, or private fields.",
        },
        {
            "id": "side_effect",
            "description": "Write operations must be intentional and must not create hidden side effects.",
        },
    ]

    def __init__(
        self,
        rules: list[dict | str] | None = None,
        llm_url: str = config_settings.ai_chat_url,
        guard: SafetyGuard | None = None,
    ):
        self._rules = rules or self.DEFAULT_RULES
        self._llm_url = llm_url
        self._guard = guard or SafetyGuard()

    def verify(
        self,
        input_data: dict,
        static_checks: list[CheckResult] | None = None,
        rules: list[dict | str] | None = None,
    ) -> CheckResult:
        """Ask the LLM whether input violates any rule; silently fallback on failure."""
        fallback = self._static_fallback(input_data, static_checks)
        try:
            reply = self._call_llm(self._build_messages(input_data, rules or self._rules))
            if not reply.strip():
                return fallback
            parsed = self._extract_json(reply)
            violated = self._as_bool(parsed.get("violated", not parsed.get("passed", True)))
            detail = parsed.get("reason") or parsed.get("detail") or "No rule violation"
            rule_id = parsed.get("rule_id")
            if rule_id:
                detail = f"{rule_id}: {detail}"
            return CheckResult(name="rule_engine_llm", passed=not violated, detail=detail)
        except Exception:
            return fallback

    def _static_fallback(self, input_data: dict, static_checks: list[CheckResult] | None = None) -> CheckResult:
        if static_checks is None:
            static_checks = [
                self._guard.check_params(input_data.get("tool", ""), input_data.get("params", {})),
                self._guard.predict_side_effect(input_data.get("tool", ""), input_data.get("result", {})),
            ]
        passed = all(check.passed for check in static_checks)
        failed = [check.name for check in static_checks if not check.passed]
        detail = "Static fallback passed" if passed else f"Static fallback failed: {failed}"
        return CheckResult(name="rule_engine_llm", passed=passed, detail=detail)

    def _build_messages(self, input_data: dict, rules: list[dict | str]) -> list[dict]:
        prompt = (
            "Judge whether the input violates any compliance or safety rule.\n"
            f"Rules: {json.dumps(rules, ensure_ascii=False)}\n"
            f"Input: {json.dumps(input_data, ensure_ascii=False)}\n\n"
            'Reply ONLY JSON: {"violated": bool, "rule_id": "...", "reason": "..."}'
        )
        return [{"role": "user", "content": prompt}]

    def _call_llm(self, messages: list[dict]) -> str:
        body = {"messages": messages, "temperature": 0.1, "max_tokens": 512}
        req = urllib.request.Request(
            self._llm_url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": ""},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as rp:
            return self._extract_reply(json.loads(rp.read().decode("utf-8")))

    @staticmethod
    def _extract_reply(payload: dict) -> str:
        if "reply" in payload:
            return payload.get("reply") or ""
        data = payload.get("data") or {}
        if "reply" in data:
            return data.get("reply") or ""
        nested = data.get("data") or {}
        return nested.get("reply") or ""

    @staticmethod
    def _extract_json(raw: str) -> dict:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            raw = raw.rsplit("```", 1)[0]
        return json.loads(raw)

    @staticmethod
    def _as_bool(value) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes"}
        return bool(value)


class Verifier:
    """Three-layer verification: assertions, rule matching, LLM."""

    def __init__(self, llm_url: str = config_settings.ai_chat_url):
        self._llm_url = llm_url
        self._layer1 = GuardLayer1()
        self._guard = SafetyGuard()
        self._rule_engine_llm = RuleEngineLLM(llm_url=llm_url, guard=self._guard)

    def verify(self, result: dict) -> bool:
        if result is None:
            raise ValueError("tool result is None")
        if result.get("needs_approval"):
            return True
        if not result.get("success", False):
            raise ValueError(result.get("error") or "tool result failed verification")
        return True

    def verify_step(self, step: PlanStep, result: dict) -> VerificationResult:
        """Run all three verification layers on a single step result."""
        checks: list[CheckResult] = []

        # Layer 1: Python assertions (free)
        checks.append(self._layer1_assertions(step, result))

        # Layer 2: DistilBERT instruction filter (free)
        layer1_result = self._layer1.predict(step.description)
        if not layer1_result["safe"]:
            return VerificationResult(
                passed=False,
                checks=[
                    CheckResult(
                        name="layer1_filter",
                        passed=False,
                        detail=f"Layer1 blocked: {layer1_result['risk_type']} (conf={layer1_result['confidence']})",
                    )
                ],
                confidence=0.0,
            )
        checks.append(
            CheckResult(
                name="layer1_filter",
                passed=True,
                detail=f"Layer1 passed (conf={layer1_result['confidence']})",
            )
        )

        # Layer 3: Rule matching + LLM rule engine with static fallback
        static_rule_checks = [
            self._guard.check_params(step.tool, step.params_template),
            self._guard.predict_side_effect(step.tool, result),
        ]
        checks.extend(static_rule_checks)
        checks.append(
            self._rule_engine_llm.verify(
                self._rule_engine_input(step, result),
                static_rule_checks,
                self._rule_engine_rules(step),
            )
        )

        # Layer 4: LLM verification (costly, on demand)
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

    @staticmethod
    def _rule_engine_input(step: PlanStep, result: dict) -> dict:
        return {
            "step_id": step.step_id,
            "description": step.description,
            "tool": step.tool,
            "params": step.params_template,
            "expected_state": step.expected_state,
            "verification_criteria": step.verification_criteria,
            "result": result,
        }

    @staticmethod
    def _rule_engine_rules(step: PlanStep) -> list[dict | str]:
        rules: list[dict | str] = list(RuleEngineLLM.DEFAULT_RULES)
        for index, criterion in enumerate(step.verification_criteria):
            rules.append({"id": f"verification_criteria_{index + 1}", "description": criterion})
        return rules

    def _call_llm(self, messages: list[dict]) -> str:
        from cloud.app.agent_runtime.runtime_llm import RuntimeLLM

        llm = RuntimeLLM()
        llm._auth_header = ""
        try:
            result = llm._call_ai(messages, temperature=0.1, force_level=2)
            return result.get("reply", "")
        except Exception:
            return ""

    @staticmethod
    def _extract_json(raw: str) -> dict:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            raw = raw.rsplit("```", 1)[0]
        return json.loads(raw)
