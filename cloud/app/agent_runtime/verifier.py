"""L4 Meta-Cognitive: Verifier — three-layer result verification (assertion, rule, LLM)."""

import json
import logging

from cloud.app.agent_runtime.guard import GuardLayer1
from cloud.app.agent_runtime.models import CheckResult, VerificationResult
from cloud.app.agent_runtime.planner import Plan, PlanStep
from cloud.app.agent_runtime.safety_guard import RuleEngineLLM, SafetyGuard
from shared.config import settings as config_settings

logger = logging.getLogger(__name__)


class Verifier:
    """Three-layer verification: assertions, rule matching, LLM."""

    def __init__(self, llm_url: str = config_settings.ai_chat_url):
        self._llm_url = llm_url
        self._layer1 = GuardLayer1()
        self._guard = SafetyGuard()
        self._rule_engine_llm = RuleEngineLLM(llm_url=llm_url, guard=self._guard)

    def verify(self, result: dict) -> bool:
        """验证工具执行结果。"""
        if result is None:
            raise ValueError("tool result is None")
        if result.get("needs_approval"):
            return True
        if not result.get("success", False):
            raise ValueError(result.get("error") or "tool result failed verification")
        return True

    def verify_step(self, step: PlanStep, result: dict) -> VerificationResult:
        """验证单个步骤的执行结果。"""
        checks: list[CheckResult] = []
        checks.append(self._layer1_assertions(step, result))
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
        checks.append(CheckResult(name="layer1_filter", passed=True, detail=f"Layer1 passed (conf={layer1_result['confidence']})"))
        static_rule_checks = [self._guard.check_params(step.tool, step.params_template), self._guard.predict_side_effect(step.tool, result)]
        checks.extend(static_rule_checks)
        checks.append(self._rule_engine_llm.verify(self._rule_engine_input(step, result), static_rule_checks, self._rule_engine_rules(step)))
        if not all(c.passed for c in checks):
            llm_check = self._layer3_llm(step, result)
            checks.append(llm_check)
        else:
            checks.append(CheckResult(name="llm_verification", passed=True, detail="Skipped — lower layers passed"))
        passed = all(c.passed for c in checks)
        confidence = sum(1.0 for c in checks if c.passed) / max(len(checks), 1)
        return VerificationResult(passed=passed, checks=checks, confidence=confidence)

    def verify_global(self, plan: Plan, results: list[dict]) -> bool:
        """验证整个计划的完成条件。"""
        if not plan.completion_conditions:
            return True
        prompt = (
            f"Plan goal: {plan.goal}\nCompletion conditions: {json.dumps(plan.completion_conditions)}\n"
            f"Step results: {json.dumps(results, ensure_ascii=False)}\n\n"
            "Are all completion conditions satisfied? Reply ONLY 'true' or 'false'."
        )
        try:
            reply = self._call_llm([{"role": "user", "content": prompt}])
            return reply.strip().lower() == "true"
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            logger.error("Global verification failed: %s", e)
            return False

    @staticmethod
    def _layer1_assertions(step: PlanStep, result: dict) -> CheckResult:
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
        prompt = (
            f"Verify the following step result:\nStep: {step.description} (tool: {step.tool})\n"
            f"Verification criteria: {json.dumps(step.verification_criteria)}\n"
            f"Result: {json.dumps(result, ensure_ascii=False)}\n\n"
            'Reply ONLY a JSON: {"passed": bool, "reason": "..."}'
        )
        try:
            reply = self._call_llm([{"role": "user", "content": prompt}])
            parsed = self._extract_json(reply)
            return CheckResult(name="llm_verification", passed=parsed.get("passed", False), detail=parsed.get("reason", "No reason given"))
        except (KeyError, ValueError, json.JSONDecodeError) as e:
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
        except (KeyError, TypeError):
            logger.warning("Verifier exception", exc_info=True)
            return ""

    @staticmethod
    def _extract_json(raw: str) -> dict:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            raw = raw.rsplit("```", 1)[0]
        return json.loads(raw)
