"""Strategy service for L1/L2/L3 compliance decisions."""

from __future__ import annotations

import sqlite3
from typing import Any, Optional

from cloud.rules.loader import load_pharma_l2_rules, load_pharma_rules, load_research_l2_rules, load_research_rules

from .audit import EnforcerAudit
from .engine import ComplianceEngine as ComplianceEnforcer
from .rules import EnforcerEngine


def _run_compliance_trigger(task: str, context: dict) -> None:
    import sqlite3

    from cloud.app.agent_runtime.compliance_trigger import compliance_monitor_trigger
    from cloud.app.agent_runtime.runtime_core import RuntimeCore
    from cloud.app.database import DB_PATH

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        runtime = RuntimeCore(conn, conn, "", "compliance_monitor")
        compliance_monitor_trigger(runtime, task, context)
    finally:
        conn.close()


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
            result = self.enforcer.check_all_levels(visit_data)
        else:
            result = {"level": "L3", "action": "log", "violations": []}
        if result["level"] in ("L1", "L2"):
            import threading

            task_desc = f"合规评估: {result.get('action', '')}"
            threading.Thread(
                target=_run_compliance_trigger,
                args=(task_desc, visit_data),
                daemon=True,
            ).start()
        return result

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
