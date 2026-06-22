"""L4 安全守卫与 LLM 规则引擎。"""

import json
import logging
import os
import urllib.request

from cloud.app.agent_runtime.core.models import CheckResult
from shared.ai_gateway import LLM_INFERENCE_TIMEOUT
from shared.config import settings as config_settings

L3_SYSTEM_PROMPT = (
    "You are a safety evaluator. Given a tool name and its parameters, "
    "predict the side effects. Return JSON with keys: risk_level (low/medium/high), "
    "effects (list of strings), recommendation (允许/需确认/禁止)."
)

logger = logging.getLogger(__name__)


class DistilBertClassifier:
    """Lazy-loaded DistilBERT classifier for instruction safety classification (L1).

    Controlled by ``SAFETY_GUARD_L1_ENABLED`` env var (default ``false``).
    On load failure silently falls back to safe classification.
    """

    _model = None
    _tokenizer = None

    @classmethod
    def is_enabled(cls) -> bool:
        """Check if L1 safety guard is enabled via environment variable."""
        return os.environ.get("SAFETY_GUARD_L1_ENABLED", "false").lower() == "true"

    @classmethod
    def _load(cls) -> bool:
        """Lazy-load transformers model and tokenizer."""
        if cls._model is not None:
            return True
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            cls._tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
            cls._model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased")
            return True
        except (OSError, ImportError):
            logger.warning("Failed to load DistilBERT model", exc_info=True)
            return False

    @classmethod
    def classify(cls, instruction: str) -> tuple[str, float]:
        """Classify instruction as ``"safe"`` or ``"unsafe"`` with confidence score.

        Returns ``("safe", 0.0)`` on load failure.
        """
        if not cls._load():
            return "safe", 0.0
        import torch

        inputs = cls._tokenizer(instruction, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = cls._model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        safe_score = probs[0][0].item()
        unsafe_score = probs[0][1].item()
        if unsafe_score > safe_score:
            return "unsafe", unsafe_score
        return "safe", safe_score


class SafetyGuard:
    """Parameter boundary check, instruction classification (L1), and side-effect prediction (L2+L3)."""

    _side_effects_cache: dict | None = None

    @classmethod
    def _load_side_effects(cls) -> dict:
        if cls._side_effects_cache is not None:
            return cls._side_effects_cache
        path = os.path.join(os.path.dirname(__file__), "side_effects.json")
        try:
            with open(path, encoding="utf-8") as f:
                cls._side_effects_cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            cls._side_effects_cache = {}
        return cls._side_effects_cache

    @staticmethod
    def check_params(tool: str, params: dict) -> CheckResult:
        """Check tool parameters for risky keys (passwords, secrets, tokens, etc.)."""
        risky_keys = {"password", "secret", "token", "key", "certificate", "private"}
        violations = [k for k in params if any(r in k.lower() for r in risky_keys)]
        return CheckResult(
            name="param_boundary",
            passed=len(violations) == 0,
            detail=f"Risky params: {violations}" if violations else "All params safe",
        )

    @classmethod
    def classify_instruction(cls, instruction: str) -> CheckResult:
        """L1 instruction classification using DistilBERT or static fallback.

        When ``SAFETY_GUARD_L1_ENABLED=true``, routes the instruction
        through DistilBERT.  When disabled or on model-load failure, falls
        back to the static ``check_params()``.
        """
        if DistilBertClassifier.is_enabled():
            try:
                label, confidence = DistilBertClassifier.classify(instruction)
                passed = label == "safe"
                return CheckResult(
                    name="instruction_classifier",
                    passed=passed,
                    detail=f"DistilBERT: {label} (confidence={confidence:.4f})",
                )
            except (ValueError, RuntimeError):
                logger.warning("DistilBERT classification failed, using static fallback", exc_info=True)
        return cls.check_params("instruction", {"instruction": instruction})

    @staticmethod
    def predict_side_effect(tool: str, params: dict) -> CheckResult:
        """Layer3 side-effect prediction using knowledge base.
        Checks side_effects.json for known effects, affected modules, and risk level.
        Returns structured risk assessment with recommendation.
        """
        effects_db = SafetyGuard._load_side_effects()
        entry = effects_db.get(tool)

        if entry:
            risk = entry.get("risk_level", "low")
            effects = entry.get("known_effects", [])
            modules = entry.get("affected_modules", [])
            recommendation = entry.get("recommendation", "允许")

            detail_parts = [f"副作用: {'; '.join(effects)}", f"影响模块: {', '.join(modules)}", f"风险等级: {risk}", f"建议: {recommendation}"]

            passed = risk != "high" or recommendation != "禁止"
            return CheckResult(
                name="side_effect",
                passed=passed,
                detail=" | ".join(detail_parts),
            )

        write_tools = {"create_notification", "write_memory", "compliance_check", "agent_brain_set"}
        is_write = tool in write_tools
        return CheckResult(
            name="side_effect",
            passed=True,
            detail=f"Write operation: {tool}" if is_write else "Read-only operation (no known side effects)",
        )

    @classmethod
    def _l3_enabled(cls) -> bool:
        """Check if L3 safety guard is enabled via environment variable."""
        return os.environ.get("SAFETY_GUARD_L3_ENABLED", "false").lower() == "true"

    @classmethod
    async def predict_side_effect_llm(
        cls,
        tool: str,
        params: dict,
        llm_service: object,
    ) -> CheckResult:
        """L3 side-effect prediction using LLM via LlmService.

        When ``SAFETY_GUARD_L3_ENABLED=true``, calls ``LlmService.generate()``
        to predict side effects.  On failure or when disabled, falls back to
        the static JSON-based ``predict_side_effect()``.

        Returns a ``CheckResult`` with risk assessment.
        """
        if not cls._l3_enabled():
            return cls.predict_side_effect(tool, params)
        try:
            prompt = (
                f"Tool: {tool}\nParams: {json.dumps(params, ensure_ascii=False)}\nPredict potential side effects, risk level, and recommendation."
            )
            reply = await llm_service.generate(prompt, context=L3_SYSTEM_PROMPT)
            parsed = json.loads(reply)
            risk = parsed.get("risk_level", "medium")
            effects = parsed.get("effects", [])
            recommendation = parsed.get("recommendation", "允许")
            passed = risk != "high" or recommendation != "禁止"
            detail_parts = [
                f"LLM副作用: {'; '.join(effects)}",
                f"风险等级: {risk}",
                f"建议: {recommendation}",
            ]
            return CheckResult(
                name="side_effect_llm",
                passed=passed,
                detail=" | ".join(detail_parts),
            )
        except Exception:  # 多种失败模式，保持宽捕获
            logger.warning("L3 LLM side-effect prediction failed, using static fallback", exc_info=True)
            return cls.predict_side_effect(tool, params)


class RuleEngineLLM:
    """LLM rule checker with static SafetyGuard fallback."""

    DEFAULT_RULES = [
        {"id": "param_boundary", "description": "Tool parameters must not expose passwords, secrets, tokens, keys, certificates, or private fields."},
        {"id": "side_effect", "description": "Write operations must be intentional and must not create hidden side effects."},
    ]

    def __init__(self, rules: list[dict | str] | None = None, llm_url: str = config_settings.ai_chat_url, guard: SafetyGuard | None = None):
        self._rules = rules or self.DEFAULT_RULES
        self._llm_url = llm_url
        self._guard = guard or SafetyGuard()

    def verify(self, input_data: dict, static_checks: list[CheckResult] | None = None, rules: list[dict | str] | None = None) -> CheckResult:
        """verify."""
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
        except Exception:  # 多种失败模式，保持宽捕获
            logger.warning("Safety guard exception, falling back", exc_info=True)
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
        with urllib.request.urlopen(req, timeout=LLM_INFERENCE_TIMEOUT) as rp:
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
