"""L1, L2, and L3 compliance enforcement services."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Optional

from cloud.rules.loader import load_pharma_l2_rules, load_pharma_rules, load_research_l2_rules, load_research_rules

from .audit import EnforcerAudit, _l1_payload
from .rules import DetectionRule, EnforcerEngine, Violation, _now


class ComplianceEngine:
    """Compliance engine coordinating rule matching and audit logging."""

    def __init__(self, db: sqlite3.Connection):
        """Initialize the compliance engine.

        Args:
            db: SQLite connection used by rules and audit logs.

        Returns:
            None.
        """
        self.db = db
        self._engine = EnforcerEngine(db)
        self._audit = EnforcerAudit(db)
        self._audit.ensure_tables()

    def check_visit(self, visit_data: dict[str, Any]) -> list[Violation]:
        """Run L1 hard-block checks for a visit.

        Args:
            visit_data: Visit payload to evaluate.

        Returns:
            List of L1 violations.
        """
        violations = self._engine.check_visit(visit_data)
        for violation in violations:
            self._audit._log_violation(violation, visit_data)
        return violations

    def get_l1_rules(self) -> list[Any]:
        """Return L1 hard-block rules.

        Args:
            None.

        Returns:
            List of parsed L1 rules.
        """
        return self._engine.get_l1_rules()

    def get_l2_rules(self) -> list[dict[str, Any]]:
        """Return L2 warning rules.

        Args:
            None.

        Returns:
            List of L2 rule dictionaries.
        """
        return self._engine.get_l2_rules()

    def check_all_levels(self, visit_data: dict[str, Any]) -> dict[str, Any]:
        """Run L1, L2, and L3 compliance checks for a visit.

        Args:
            visit_data: Visit payload to evaluate.

        Returns:
            Evaluation result with level, action, and violations.
        """
        data = visit_data or {}
        l1 = self.check_visit(data)
        if l1:
            return {"level": "L1", "action": "block", "violations": _l1_payload(l1)}
        l2 = self.check_visit_l2(data)
        if l2:
            self._audit._log_l2_batch(l2, data)
            return {"level": "L2", "action": "warn", "violations": l2}
        self._audit._log_l3(data)
        return {"level": "L3", "action": "log", "violations": []}

    def check_visit_l2(self, visit_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Run L2 soft-warning checks for a visit.

        Args:
            visit_data: Visit payload to evaluate.

        Returns:
            List of L2 violation dictionaries.
        """
        return self._engine.check_visit_l2(visit_data)


ComplianceEnforcer = ComplianceEngine


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
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS research_enforcement_log (id INTEGER PRIMARY KEY AUTOINCREMENT, rule_code TEXT NOT NULL, rule_name TEXT NOT NULL, severity TEXT NOT NULL, action TEXT NOT NULL, visit_data_json TEXT NOT NULL, created_at TEXT NOT NULL)"
        )
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
                "INSERT INTO research_enforcement_log (rule_code, rule_name, severity, action, visit_data_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
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


class ComplianceStrategyService:
    """Strategy service for L1/L2/L3 compliance decisions."""

    def __init__(self, db: sqlite3.Connection | None):
        """Initialize the compliance strategy service.

        Args:
            db: Optional SQLite connection used by rule checks and audit logs.

        Returns:
            None.
        """
        self.db = db
        self.enforcer = ComplianceEnforcer(db) if db else None
        self._all_l2_rules = load_pharma_l2_rules() + load_research_l2_rules()
        if db:
            EnforcerAudit(db)._ensure_l2_tables()

    def evaluate_visit(self, visit_data: dict[str, Any]) -> dict[str, Any]:
        """Evaluate one visit through the full compliance strategy.

        Args:
            visit_data: Visit payload to evaluate.

        Returns:
            Evaluation result with level, action, and violations.
        """
        if self.enforcer:
            return self.enforcer.check_all_levels(visit_data)
        return {"level": "L3", "action": "log", "violations": []}

    def _check_l2_rules(self, visit_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Run all strategy L2 rules for a visit.

        Args:
            visit_data: Visit payload to evaluate.

        Returns:
            List of matched L2 violations.
        """
        return EnforcerEngine(self.db).check_l2_rules(self._all_l2_rules, visit_data)

    def _match_l2_rule(self, rule: dict[str, Any], visit_data: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Match one L2 rule for test and strategy callers.

        Args:
            rule: L2 rule dictionary.
            visit_data: Visit payload to evaluate.

        Returns:
            L2 violation dictionary when matched, otherwise None.
        """
        return EnforcerEngine(self.db)._match_l2(rule, visit_data)

    def _log_l2(self, violations: list[dict[str, Any]], visit_data: dict[str, Any]) -> None:
        """Log L2 violations for a visit.

        Args:
            violations: L2 violation dictionaries to log.
            visit_data: Original visit payload.

        Returns:
            None.
        """
        EnforcerAudit(self.db)._log_l2_batch(violations, visit_data)

    def _log_l3(self, visit_data: dict[str, Any]) -> None:
        """Log an L3 pass-through visit.

        Args:
            visit_data: Visit payload to log.

        Returns:
            None.
        """
        EnforcerAudit(self.db)._log_l3(visit_data)

    def get_strategy(self, rule_id: str) -> Optional[dict[str, Any]]:
        """Return strategy metadata for a rule id.

        Args:
            rule_id: L1 code or L2 id to look up.

        Returns:
            Strategy metadata when found, otherwise None.
        """
        for rules in (load_pharma_rules(), load_research_rules()):
            for rule in rules:
                if rule.get("code") == rule_id:
                    return {"rule_id": rule_id, "level": "L1", "action": "block", "severity": rule.get("severity")}
        for rule in self._all_l2_rules:
            if rule.get("id") == rule_id:
                severity = rule.get("severity")
                return {"rule_id": rule_id, "level": "L2", "action": "warn" if severity in ("warning",) else "review", "severity": severity}
        return None

    def get_l2_rules(self) -> list[dict[str, Any]]:
        """Return all strategy L2 rules.

        Args:
            None.

        Returns:
            List of L2 rule dictionaries.
        """
        return self._all_l2_rules
