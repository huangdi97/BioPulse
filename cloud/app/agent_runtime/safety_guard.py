"""L4 安全守卫与 LLM 规则引擎。"""

import json
import os
import urllib.request

from cloud.app.agent_runtime.models import CheckResult
from shared.config import settings as config_settings


class SafetyGuard:
    """Parameter boundary check and side-effect prediction (L1+L2+L3)."""

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
        risky_keys = {"password", "secret", "token", "key", "certificate", "private"}
        violations = [k for k in params if any(r in k.lower() for r in risky_keys)]
        return CheckResult(
            name="param_boundary",
            passed=len(violations) == 0,
            detail=f"Risky params: {violations}" if violations else "All params safe",
        )

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
