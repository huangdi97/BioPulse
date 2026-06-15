"""Failure classification — non-LLM pattern matching first, LLM fallback for complex cases."""

import json
import logging
from typing import Any

from cloud.app.agent_runtime.analyzer.models import Analysis
from cloud.app.agent_runtime.runtime_llm.request import raw_llm_call
from shared.config import settings as config_settings

logger = logging.getLogger(__name__)


def call_llm(llm_url: str, messages: list[dict], auth_header: str = "") -> str:
    body = {"messages": messages, "temperature": 0.1, "max_tokens": 1024}
    result = raw_llm_call(body, auth_header, url=llm_url)
    return result.get("data", {}).get("reply", "")


def extract_json(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0]
    return json.loads(raw)


class FailureClassifier:
    """Classifies step failures — non-LLM pattern matching, LLM fallback for complex cases."""

    STATIC_PATTERNS: dict[str, tuple[str, str]] = {
        "timeout": ("timeout", "Increase timeout or split into sub-steps"),
        "timed out": ("timeout", "Increase timeout or split into sub-steps"),
        "permission denied": ("permission_denied", "Check caller permissions or request approval"),
        "permission_denied": ("permission_denied", "Check caller permissions or request approval"),
        "circuit breaker": ("tool_unavailable", "Wait for circuit breaker to reset or retry later"),
        "unknown tool": ("tool_unavailable", "Verify tool name in tool registry"),
        "database is locked": ("data_lock", "Retry when database is not busy"),
        "empty": ("data_empty", "No data returned — verify query parameters"),
        "no data": ("data_empty", "No data returned — verify query parameters"),
        "not found": ("data_empty", "Resource not found — check identifiers"),
        "invalid action": ("plan_invalid", "LLM generated invalid action — check prompt constraints"),
        "failed to parse": ("plan_invalid", "LLM output not parseable — check model response format"),
        "budget_exceeded": ("budget_exceeded", "Cost budget exceeded — reduce scope or increase budget"),
    }

    CATEGORY_TO_SEVERITY = {
        "timeout": "medium",
        "permission_denied": "high",
        "tool_unavailable": "medium",
        "data_lock": "low",
        "data_empty": "low",
        "plan_invalid": "high",
        "budget_exceeded": "high",
        "logical_error": "medium",
        "context_drift": "medium",
    }

    def __init__(self, llm_url: str = config_settings.ai_chat_url, auth_header: str = ""):
        self._llm_url = llm_url
        self._auth_header = auth_header

    def analyze(self, task: str, failed_step: str, result: dict, context: dict | None = None) -> Analysis:
        """Main entry — try non-LLM first, fall back to LLM for complex failures."""
        ctx = context or {}

        category = self.categorize_failure(result)
        severity = self.CATEGORY_TO_SEVERITY.get(category, "low")
        suggestion = self._static_suggestion(category)

        if category not in ("logical_error", "context_drift", "unknown"):
            return Analysis(cause=category, severity=severity, suggestion=suggestion)

        return self._llm_analysis(task, failed_step, result, ctx)

    def categorize_failure(self, result: dict) -> str:
        """Classify failure type without LLM — pattern matching on error text."""
        error = result.get("error", "") or ""
        error_lower = error.lower()

        for pattern, (category, _) in self.STATIC_PATTERNS.items():
            if pattern in error_lower:
                return category

        success = result.get("success", False)
        if success:
            data = result.get("data")
            if data is None or (isinstance(data, list) and len(data) == 0):
                return "data_empty"
            return "success"

        if "logical" in error_lower or "invalid" in error_lower:
            return "logical_error"

        return "unknown"

    def _llm_analysis(self, task: str, failed_step: str, result: dict, context: dict) -> Analysis:
        """Use LLM to diagnose complex failures (logical error, plan_invalid, context_drift)."""
        prompt = (
            f"Task: {task}\n"
            f"Failed step: {failed_step}\n"
            f"Result: {json.dumps(result, ensure_ascii=False)}\n"
            f"Context: {json.dumps(context, ensure_ascii=False)}\n\n"
            "Analyze the failure. Reply ONLY JSON: "
            '{"cause": "logical_error"|"plan_invalid"|"context_drift"|"unknown", '
            '"severity": "low"|"medium"|"high", "suggestion": "..."}'
        )
        try:
            reply = call_llm(self._llm_url, [{"role": "user", "content": prompt}], self._auth_header)
            parsed = extract_json(reply)
            return Analysis(
                cause=parsed.get("cause", "unknown"),
                severity=parsed.get("severity", "medium"),
                suggestion=parsed.get("suggestion", "No suggestion"),
            )
        except Exception as e:
            logger.error("LLM analysis failed: %s", e)
            return Analysis(cause="unknown", severity="medium", suggestion="LLM analysis unavailable")

    @staticmethod
    def _static_suggestion(category: str) -> str:
        suggestions = {
            "timeout": "Increase timeout or split into sub-steps",
            "permission_denied": "Check caller permissions or request approval",
            "tool_unavailable": "Wait for circuit breaker to reset or retry later",
            "data_lock": "Retry when database is not busy",
            "data_empty": "Verify query parameters or data source",
            "plan_invalid": "Check plan structure and LLM prompt constraints",
            "budget_exceeded": "Reduce scope or increase cost budget",
        }
        return suggestions.get(category, "Review logs and retry with adjusted parameters")
