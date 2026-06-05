"""Data-driven compliance rule enforcer.

Detection rules are defined in JSON files (pharma_rules.json, research_rules.json)
and loaded at runtime. Adding a new rule only requires editing the JSON file,
not modifying Python code.
"""

import json
import sqlite3
from datetime import datetime, timezone
from typing import List

from cloud.rules.loader import (
    load_research_rules,
)

from .compliance_enforcer_audit import EnforcerAudit
from .compliance_enforcer_engine import (
    EnforcerEngine,
    Violation,
)


class ComplianceEnforcer:
    """Enforces compliance rules against visit data using JSON-defined detection logic."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self._engine = EnforcerEngine(db)
        self._audit = EnforcerAudit(db)
        self._audit.ensure_tables()

    def check_visit(self, visit_data: dict) -> List[Violation]:
        """Check visit data against all L1 rules. Returns list of violations."""
        violations = self._engine.check_visit(visit_data)
        for v in violations:
            self._audit._log_violation(v, visit_data)
        return violations

    def get_l1_rules(self) -> list:
        """Return all parsed L1 detection rules."""
        return self._engine.get_l1_rules()

    def get_l2_rules(self) -> list:
        return self._engine.get_l2_rules()

    def check_all_levels(self, visit_data: dict) -> dict:
        visit_data = visit_data or {}
        l1_violations = self.check_visit(visit_data)
        if l1_violations:
            return {
                "level": "L1",
                "action": "block",
                "violations": [
                    {
                        "rule_code": v.rule_code,
                        "rule_name": v.rule_name,
                        "severity": v.severity,
                        "action": v.action,
                        "detail": v.detail,
                    }
                    for v in l1_violations
                ],
            }
        l2_violations = self._engine.check_visit_l2(visit_data)
        if l2_violations:
            self._audit._log_l2_batch(l2_violations, visit_data)
            return {"level": "L2", "action": "warn", "violations": l2_violations}
        self._audit._log_l3(visit_data)
        return {"level": "L3", "action": "log", "violations": []}

    def check_visit_l2(self, visit_data: dict) -> list:
        return self._engine.check_visit_l2(visit_data)


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
