"""Research-mode compliance enforcer backed by research rules."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from cloud.rules.loader import load_research_rules

from .rules import DetectionRule, Violation, _now


class ResearchComplianceEnforcer:
    """Research-mode compliance enforcer backed by research rules."""

    def __init__(self, db: sqlite3.Connection):
        """Initialize the research compliance enforcer.

        Args:
            db: SQLite connection used for audit logs.

        Returns:
            None.
        """
        self.db = db
        self._rules = load_research_rules()
        self._parsed_rules = [self._parse_rule(r) for r in self._rules]
        self.db.execute("""CREATE TABLE IF NOT EXISTS research_enforcement_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_code TEXT NOT NULL,
            rule_name TEXT NOT NULL,
            severity TEXT NOT NULL,
            action TEXT NOT NULL,
            visit_data_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        self.db.commit()

    def _parse_rule(self, rule: dict[str, Any]) -> DetectionRule:
        """Parse a raw research rule dict into a DetectionRule.

        Args:
            rule: Raw rule loaded from research_rules.json.

        Returns:
            Parsed DetectionRule instance.
        """
        detection = rule.get("detection", {})
        fields = detection.get("fields") or (detection.get("field") and [detection.get("field")]) or []
        return DetectionRule(
            rule.get("code", ""),
            rule.get("name", ""),
            rule.get("level", ""),
            rule.get("action", ""),
            rule.get("severity", ""),
            detection.get("type", ""),
            fields[0] if fields else detection.get("field", ""),
            detection.get("operator") or ("eq" if detection.get("condition") == "missing" else "eq"),
            detection.get("value", ""),
            detection.get("keywords", []),
            detection.get("exclude_when", {}),
        )

    def _match_l1(self, rule: DetectionRule, data: dict[str, Any]) -> bool:
        """Match one parsed L1 rule against visit data.

        Args:
            rule: Parsed DetectionRule.
            data: Visit payload to evaluate.

        Returns:
            True when the rule matches, otherwise False.
        """
        exclude = rule.exclude_when
        if exclude and exclude.get("operator") == "eq" and data.get(exclude.get("field")) == exclude.get("value"):
            return False
        if rule.detection_type == "keyword_match":
            raw_rule = next((r for r in self._rules if r.get("code") == rule.code), {})
            fields = (raw_rule.get("detection") or {}).get("fields", [rule.detection_field])
            for field in fields:
                val = data.get(field)
                if val and any(kw in str(val) for kw in rule.keywords):
                    return True
            return False
        if rule.detection_type == "threshold":
            from cloud.app.compliance.condition_evaluator import _compare

            return _compare(data.get(rule.detection_field), rule.operator, rule.value)
        if rule.detection_type == "field_check":
            val = data.get(rule.detection_field)
            if rule.operator == "eq":
                return val == rule.value
            if rule.operator == "neq":
                return val != rule.value
        return False

    def check_research_visit(self, visit_data: dict[str, Any]) -> list[Violation]:
        """Run research L1 rules and write enforcement logs.

        Args:
            visit_data: Research visit payload to evaluate.

        Returns:
            List of research violations.
        """
        violations = []
        data = visit_data or {}
        for rule in self._parsed_rules:
            if rule.level != "L1":
                continue
            if not self._match_l1(rule, data):
                continue
            violation = Violation(
                rule.code,
                rule.name,
                rule.severity,
                rule.action,
                f"Research rule '{rule.code}' triggered: {rule.name}",
            )
            violations.append(violation)
            self.db.execute(
                "INSERT INTO research_enforcement_log "
                "(rule_code, rule_name, severity, action, visit_data_json, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (violation.rule_code, violation.rule_name, violation.severity, violation.action, json.dumps(data, ensure_ascii=False), _now()),
            )
            self.db.commit()
        return violations

    def get_l1_rules(self) -> list[dict[str, Any]]:
        """Return research L1 hard-block rules.

        Args:
            None.

        Returns:
            List of research L1 rules.
        """
        return [rule for rule in self._rules if rule.get("level") == "L1"]
