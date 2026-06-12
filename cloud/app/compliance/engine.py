"""L1, L2, and L3 compliance engine — coordination layer."""

from __future__ import annotations

import sqlite3
from typing import Any

from .audit import EnforcerAudit, _l1_payload
from .rules import EnforcerEngine, Violation


class ComplianceEngine:
    """Compliance engine coordinating rule matching and audit logging."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self._engine = EnforcerEngine(db)
        self._audit = EnforcerAudit(db)
        self._audit.ensure_tables()

    def check_visit(self, visit_data: dict[str, Any]) -> list[Violation]:
        violations = self._engine.check_visit(visit_data)
        for violation in violations:
            self._audit._log_violation(violation, visit_data)
        return violations

    def get_l1_rules(self) -> list[Any]:
        return self._engine.get_l1_rules()

    def get_l2_rules(self) -> list[dict[str, Any]]:
        return self._engine.get_l2_rules()

    def check_all_levels(self, visit_data: dict[str, Any]) -> dict[str, Any]:
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
        return self._engine.check_visit_l2(visit_data)


ComplianceEnforcer = ComplianceEngine
