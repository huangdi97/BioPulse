"""Data-driven compliance rule enforcer.

Detection rules are defined in JSON files (pharma_rules.json, research_rules.json)
and loaded at runtime. Adding a new rule only requires editing the JSON file,
not modifying Python code.
"""

from dataclasses import dataclass, asdict, field
from typing import List
import json
import sqlite3
from datetime import datetime, timezone

from cloud.rules.loader import (
    load_pharma_rules,
    load_research_rules,
    load_pharma_l2_rules,
    load_research_l2_rules,
)


@dataclass
class Violation:
    """A single compliance rule violation."""
    rule_code: str
    rule_name: str
    severity: str
    action: str
    detail: str


@dataclass
class DetectionRule:
    """A parsed detection rule with its matching logic."""
    code: str
    name: str
    level: str
    action: str
    severity: str
    detection_type: str
    detection_field: str
    operator: str
    value: object
    keywords: list = field(default_factory=list)
    exclude_when: dict = field(default_factory=dict)


class ComplianceEnforcer:
    """Enforces compliance rules against visit data using JSON-defined detection logic."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self._rules = load_pharma_rules()
        self._parsed_rules = [self._parse_rule(r) for r in self._rules]
        self._l2_rules = load_pharma_l2_rules() + load_research_l2_rules()
        self._ensure_table()
        self._ensure_l2_tables()

    def _ensure_table(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS enforcement_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_code TEXT NOT NULL,
                rule_name TEXT NOT NULL,
                severity TEXT NOT NULL,
                action TEXT NOT NULL,
                visit_data_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        self.db.commit()

    def _parse_rule(self, rule: dict) -> DetectionRule:
        """Parse a raw rule dict from JSON into a DetectionRule object."""
        detection = rule.get("detection", {})
        return DetectionRule(
            code=rule.get("code", ""),
            name=rule.get("name", ""),
            level=rule.get("level", ""),
            action=rule.get("action", ""),
            severity=rule.get("severity", ""),
            detection_type=detection.get("type", ""),
            detection_field=detection.get("field", ""),
            operator=detection.get("operator", ""),
            value=detection.get("value", ""),
            keywords=detection.get("keywords", []),
            exclude_when=detection.get("exclude_when", {}),
        )

    def check_visit(self, visit_data: dict) -> List[Violation]:
        """Check visit data against all L1 rules. Returns list of violations."""
        visit_data = visit_data or {}
        visit_data["notes"] = (visit_data.get("notes") or "")[:5000]
        visit_data["expenses"] = max(0, visit_data.get("expenses") or 0)
        violations = []

        for rule in self._parsed_rules:
            if rule.level != "L1":
                continue

            violation = self._match_rule(rule, visit_data)
            if violation:
                violations.append(violation)

        for v in violations:
            self._log_violation(v, visit_data)

        return violations

    def _match_rule(self, rule: DetectionRule, visit_data: dict):
        """Match a single detection rule against visit data. Returns Violation or None."""
        field_value = visit_data.get(rule.detection_field)

        # Check exclusion condition first
        if rule.exclude_when:
            ex_field = rule.exclude_when.get("field")
            ex_op = rule.exclude_when.get("operator")
            ex_val = rule.exclude_when.get("value")
            ex_field_value = visit_data.get(ex_field)
            if ex_op == "eq" and ex_field_value == ex_val:
                return None

        if rule.detection_type == "keyword_match":
            if self._keyword_match(field_value, rule.keywords):
                return self._build_violation(rule)

        elif rule.detection_type == "threshold":
            if self._threshold_check(field_value, rule.operator, rule.value):
                return self._build_violation(rule)

        elif rule.detection_type == "field_check":
            if self._field_check(field_value, rule.operator, rule.value):
                return self._build_violation(rule)

        return None

    def _keyword_match(self, field_value, keywords) -> bool:
        """Check if a text field contains any of the forbidden keywords."""
        if not field_value or not keywords:
            return False
        field_str = str(field_value)
        return any(kw in field_str for kw in keywords)

    def _threshold_check(self, field_value, operator, threshold) -> bool:
        """Check if a numeric field exceeds/meets a threshold."""
        try:
            val = float(field_value) if field_value is not None else 0
            thr = float(threshold)
        except (TypeError, ValueError):
            return False

        if operator == "gte":
            return val >= thr
        elif operator == "gt":
            return val > thr
        elif operator == "lte":
            return val <= thr
        elif operator == "lt":
            return val < thr
        elif operator == "eq":
            return val == thr
        return False

    def _field_check(self, field_value, operator, expected) -> bool:
        """Check if a field equals or does not equal an expected value."""
        if operator == "eq":
            return field_value == expected
        elif operator == "neq":
            return field_value != expected
        return False

    def _build_violation(self, rule: DetectionRule) -> Violation:
        """Build a Violation object from a matched rule."""
        return Violation(
            rule_code=rule.code,
            rule_name=rule.name,
            severity=rule.severity,
            action=rule.action,
            detail=f"Rule '{rule.code}' triggered: {rule.name}",
        )

    def _log_violation(self, violation: Violation, visit_data: dict):
        self.db.execute(
            "INSERT INTO enforcement_log (rule_code, rule_name, severity, action, visit_data_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                violation.rule_code,
                violation.rule_name,
                violation.severity,
                violation.action,
                json.dumps(visit_data, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.db.commit()

    def get_l1_rules(self) -> list:
        """Return all parsed L1 detection rules."""
        return [r for r in self._parsed_rules if r.level == "L1"]

    def _ensure_l2_tables(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS compliance_l2_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT NOT NULL,
                rule_name TEXT NOT NULL,
                severity TEXT NOT NULL,
                check_type TEXT NOT NULL,
                visit_data_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS compliance_l3_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visit_data_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        self.db.commit()

    def get_l2_rules(self) -> list:
        return self._l2_rules

    def check_all_levels(self, visit_data: dict) -> dict:
        visit_data = visit_data or {}
        l1_violations = self.check_visit(visit_data)
        if l1_violations:
            return {
                "level": "L1",
                "action": "block",
                "violations": [
                    {"rule_code": v.rule_code, "rule_name": v.rule_name,
                     "severity": v.severity, "action": v.action, "detail": v.detail}
                    for v in l1_violations
                ],
            }
        l2_violations = self.check_visit_l2(visit_data)
        if l2_violations:
            self._log_l2_batch(l2_violations, visit_data)
            return {"level": "L2", "action": "warn", "violations": l2_violations}
        self._log_l3(visit_data)
        return {"level": "L3", "action": "log", "violations": []}

    def check_visit_l2(self, visit_data: dict) -> list:
        visit_data = visit_data or {}
        violations = []
        for rule in self._l2_rules:
            v = self._match_l2_rule(rule, visit_data)
            if v:
                violations.append(v)
        return violations

    def _match_l2_rule(self, rule: dict, visit_data: dict):
        check_type = rule.get("check_type")
        condition = rule.get("condition", {})
        threshold = rule.get("threshold")
        if check_type == "value_threshold":
            field = condition.get("field")
            op = condition.get("operator", "gt")
            field_val = visit_data.get(field)
            try:
                val = float(field_val) if field_val is not None else 0
                thr = float(threshold)
                if (op == "gt" and val > thr) or (op == "gte" and val >= thr):
                    return self._build_l2_violation(rule, f"值[{val}]超过阈值[{thr}]")
            except (TypeError, ValueError):
                pass
        elif check_type == "flag_check":
            field = condition.get("field")
            expected = condition.get("expected")
            if visit_data.get(field) != expected:
                return self._build_l2_violation(rule, f"字段[{field}]期望值[{expected}]，实际[{visit_data.get(field)}]")
        elif check_type == "frequency_count":
            field = condition.get("field")
            window_days = condition.get("window_days", 7)
            entity_id = visit_data.get(field)
            if entity_id is not None:
                from datetime import datetime, timedelta
                since = (datetime.now() - timedelta(days=window_days)).isoformat()
                count = self.db.execute(
                    f"SELECT COUNT(*) AS c FROM visits WHERE {field} = ? AND created_at >= ?",
                    (entity_id, since),
                ).fetchone()["c"]
                if count >= int(threshold):
                    return self._build_l2_violation(rule, f"实体[{entity_id}]在{window_days}天内拜访{count}次")
        elif check_type == "concentration_check":
            field = condition.get("field")
            ratio_threshold = condition.get("ratio_threshold", 0.8)
            window_days = condition.get("window_days", 30)
            dept_val = visit_data.get(field)
            if dept_val is not None:
                from datetime import datetime, timedelta
                since = (datetime.now() - timedelta(days=window_days)).isoformat()
                total = self.db.execute(
                    "SELECT COUNT(*) AS c FROM visits WHERE created_at >= ?", (since,)
                ).fetchone()["c"]
                if total > 0:
                    dept_count = self.db.execute(
                        f"SELECT COUNT(*) AS c FROM visits WHERE {field} = ? AND created_at >= ?",
                        (dept_val, since),
                    ).fetchone()["c"]
                    ratio = dept_count / total
                    if ratio >= ratio_threshold:
                        return self._build_l2_violation(rule, f"值[{dept_val}]占比{ratio:.1%}")
        return None

    def _build_l2_violation(self, rule: dict, detail: str = "") -> dict:
        return {
            "rule_id": rule.get("id"),
            "rule_name": rule.get("name"),
            "severity": rule.get("severity"),
            "check_type": rule.get("check_type"),
            "detail": f"L2规则'{rule.get('id')}'触发: {rule.get('name')}. {detail}",
        }

    def _log_l2_batch(self, violations: list, visit_data: dict):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        for v in violations:
            self.db.execute(
                "INSERT INTO compliance_l2_log (rule_id, rule_name, severity, check_type, visit_data_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (v["rule_id"], v["rule_name"], v["severity"], v["check_type"], json.dumps(visit_data, ensure_ascii=False), now),
            )
        self.db.commit()

    def _log_l3(self, visit_data: dict):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        self.db.execute(
            "INSERT INTO compliance_l3_log (visit_data_json, created_at) VALUES (?, ?)",
            (json.dumps(visit_data, ensure_ascii=False), now),
        )
        self.db.commit()


class ResearchComplianceEnforcer:
    """Enforces research compliance rules against visit data using research_rules.json."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self._rules = load_research_rules()
        self._ensure_table()

    def _ensure_table(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS research_enforcement_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_code TEXT NOT NULL,
                rule_name TEXT NOT NULL,
                severity TEXT NOT NULL,
                action TEXT NOT NULL,
                visit_data_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        self.db.commit()

    def check_research_visit(self, visit_data: dict) -> List[Violation]:
        violations = []
        for rule in self._rules:
            if rule.get("level") != "L1":
                continue
            violation = Violation(
                rule_code=rule["code"],
                rule_name=rule["name"],
                severity=rule.get("severity", "critical"),
                action=rule.get("action", "block"),
                detail=f"Research rule '{rule['code']}' triggered: {rule['name']}",
            )
            violations.append(violation)
            self._log_violation(violation, visit_data)
        return violations

    def _log_violation(self, violation: Violation, visit_data: dict):
        self.db.execute(
            "INSERT INTO research_enforcement_log (rule_code, rule_name, severity, action, visit_data_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                violation.rule_code,
                violation.rule_name,
                violation.severity,
                violation.action,
                json.dumps(visit_data, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.db.commit()

    def get_l1_rules(self) -> list:
        return [r for r in self._rules if r.get("level") == "L1"]
