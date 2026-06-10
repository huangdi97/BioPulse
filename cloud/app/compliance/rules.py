"""Compliance rule loading, parsing, and violation evaluation."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from cloud.app.compliance.condition_evaluator import _compare
from cloud.app.compliance.condition_evaluator import (
    _match_citation_check,
    _match_concentration_check,
    _match_discount_check,
    _match_expiry_check,
    _match_flag_check,
    _match_frequency_count,
    _match_value_threshold,
)
from cloud.rules.loader import load_pharma_l2_rules, load_pharma_rules, load_research_l2_rules

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Violation:
    """Compliance violation produced by a rule match."""

    rule_code: str
    rule_name: str
    severity: str
    action: str
    detail: str


@dataclass
class DetectionRule:
    """Parsed detection rule used by the compliance engine."""

    code: str
    name: str
    level: str
    action: str
    severity: str
    detection_type: str
    detection_field: str
    operator: str
    value: object
    keywords: list[str] = field(default_factory=list)
    exclude_when: dict[str, Any] = field(default_factory=dict)


class EnforcerEngine:
    """Rule enforcer for L1 hard blocks and L2 warnings."""

    def __init__(self, db: sqlite3.Connection):
        """Initialize the rule enforcer.

        Args:
            db: SQLite connection used by frequency and concentration checks.

        Returns:
            None.
        """
        self.db = db
        self._rules = load_pharma_rules()
        self._parsed_rules = [self._parse_rule(rule) for rule in self._rules]
        self._l2_rules = load_pharma_l2_rules() + load_research_l2_rules()

    def _parse_rule(self, rule: dict[str, Any]) -> DetectionRule:
        """Parse a raw rule dictionary into a detection rule.

        Args:
            rule: Raw rule loaded from the rule files.

        Returns:
            Parsed DetectionRule instance.
        """
        detection = rule.get("detection", {})
        return DetectionRule(
            rule.get("code", ""),
            rule.get("name", ""),
            rule.get("level", ""),
            rule.get("action", ""),
            rule.get("severity", ""),
            detection.get("type", ""),
            detection.get("field", ""),
            detection.get("operator", ""),
            detection.get("value", ""),
            detection.get("keywords", []),
            detection.get("exclude_when", {}),
        )

    def check_visit(self, visit_data: dict[str, Any]) -> list[Violation]:
        """Run all L1 hard-block rules against a visit payload.

        Args:
            visit_data: Visit payload to evaluate.

        Returns:
            List of matched L1 violations.
        """
        data = visit_data or {}
        data["notes"] = (data.get("notes") or "")[:5000]
        data["expenses"] = max(0, data.get("expenses") or 0)
        return [v for rule in self._parsed_rules if rule.level == "L1" for v in [self._match_l1(rule, data)] if v]

    def _match_l1(self, rule: DetectionRule, data: dict[str, Any]) -> Optional[Violation]:
        """Match one L1 rule against one visit payload.

        Args:
            rule: Parsed L1 rule.
            data: Visit payload to evaluate.

        Returns:
            Violation when the rule matches, otherwise None.
        """
        value = data.get(rule.detection_field)
        exclude = rule.exclude_when
        if exclude and exclude.get("operator") == "eq" and data.get(exclude.get("field")) == exclude.get("value"):
            return None
        if rule.detection_type == "keyword_match" and value and any(keyword in str(value) for keyword in rule.keywords):
            return self._l1_violation(rule)
        if rule.detection_type == "threshold" and _compare(value, rule.operator, rule.value):
            return self._l1_violation(rule)
        if rule.detection_type == "field_check":
            matched = (rule.operator == "eq" and value == rule.value) or (rule.operator == "neq" and value != rule.value)
            return self._l1_violation(rule) if matched else None
        return None

    def _l1_violation(self, rule: DetectionRule) -> Violation:
        return Violation(rule.code, rule.name, rule.severity, rule.action, f"Rule '{rule.code}' triggered: {rule.name}")

    def get_l1_rules(self) -> list[DetectionRule]:
        return [rule for rule in self._parsed_rules if rule.level == "L1"]

    def get_l2_rules(self) -> list[dict[str, Any]]:
        return self._l2_rules

    def check_visit_l2(self, visit_data: dict[str, Any]) -> list[dict[str, Any]]:
        return self.check_l2_rules(self._l2_rules, visit_data or {})

    def check_l2_rules(self, rules: list[dict[str, Any]], visit_data: dict[str, Any]) -> list[dict[str, Any]]:
        return [v for rule in rules for v in [self._match_l2(rule, visit_data or {})] if v]

    def _match_l2(self, rule: dict[str, Any], data: dict[str, Any]) -> Optional[dict[str, Any]]:
        check_type = rule.get("check_type")
        condition = rule.get("condition", {})
        threshold = rule.get("threshold")
        if check_type == "value_threshold":
            return _match_value_threshold(rule, data, condition, threshold)
        if check_type == "flag_check":
            return _match_flag_check(rule, data, condition)
        if check_type == "frequency_count":
            return _match_frequency_count(self.db, rule, data, condition, threshold)
        if check_type == "concentration_check":
            return _match_concentration_check(self.db, rule, data, condition)
        if check_type == "citation_check":
            return _match_citation_check(rule, data, condition)
        if check_type == "expiry_check":
            return _match_expiry_check(rule, data, condition)
        if check_type == "discount_check":
            return _match_discount_check(rule, data, condition, threshold)
        return None
