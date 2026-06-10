"""Compliance audit logging for L1, L2, and L3 enforcement results."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from .rules import Violation, _now


class EnforcerAudit:
    """Audit log writer for compliance enforcement events."""

    def __init__(self, db: sqlite3.Connection):
        """Initialize the audit log writer.

        Args:
            db: SQLite connection used for audit tables.

        Returns:
            None.
        """
        self.db = db

    def _ensure_table(self) -> None:
        """Ensure the L1 enforcement log table exists.

        Args:
            None.

        Returns:
            None.
        """
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS enforcement_log (id INTEGER PRIMARY KEY AUTOINCREMENT, rule_code TEXT NOT NULL, rule_name TEXT NOT NULL, severity TEXT NOT NULL, action TEXT NOT NULL, visit_data_json TEXT NOT NULL, created_at TEXT NOT NULL)"
        )
        self.db.commit()

    def _ensure_l2_tables(self) -> None:
        """Ensure the L2 and L3 audit log tables exist.

        Args:
            None.

        Returns:
            None.
        """
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS compliance_l2_log (id INTEGER PRIMARY KEY AUTOINCREMENT, rule_id TEXT NOT NULL, rule_name TEXT NOT NULL, severity TEXT NOT NULL, check_type TEXT NOT NULL, visit_data_json TEXT NOT NULL, created_at TEXT NOT NULL)"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS compliance_l3_log (id INTEGER PRIMARY KEY AUTOINCREMENT, visit_data_json TEXT NOT NULL, created_at TEXT NOT NULL)"
        )
        self.db.commit()

    def ensure_tables(self) -> None:
        """Ensure all compliance audit tables exist.

        Args:
            None.

        Returns:
            None.
        """
        self._ensure_table()
        self._ensure_l2_tables()

    def _log_violation(self, violation: Violation, visit_data: dict[str, Any]) -> None:
        """Write one L1 violation audit entry.

        Args:
            violation: L1 violation to log.
            visit_data: Original visit payload.

        Returns:
            None.
        """
        self.db.execute(
            "INSERT INTO enforcement_log (rule_code, rule_name, severity, action, visit_data_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (violation.rule_code, violation.rule_name, violation.severity, violation.action, json.dumps(visit_data, ensure_ascii=False), _now()),
        )
        self.db.commit()

    def _log_l2_batch(self, violations: list[dict[str, Any]], visit_data: dict[str, Any]) -> None:
        """Write L2 violation audit entries in one transaction.

        Args:
            violations: L2 violation dictionaries to log.
            visit_data: Original visit payload.

        Returns:
            None.
        """
        payload, now = json.dumps(visit_data, ensure_ascii=False), _now()
        for violation in violations:
            self.db.execute(
                "INSERT INTO compliance_l2_log (rule_id, rule_name, severity, check_type, visit_data_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (violation["rule_id"], violation["rule_name"], violation["severity"], violation["check_type"], payload, now),
            )
        self.db.commit()

    def _log_l3(self, visit_data: dict[str, Any]) -> None:
        """Write an L3 pass-through audit entry.

        Args:
            visit_data: Visit payload that passed L1 and L2 checks.

        Returns:
            None.
        """
        self.db.execute(
            "INSERT INTO compliance_l3_log (visit_data_json, created_at) VALUES (?, ?)", (json.dumps(visit_data, ensure_ascii=False), _now())
        )
        self.db.commit()


def _l1_payload(violations: list[Violation]) -> list[dict[str, Any]]:
    """Serialize L1 violations for API responses.

    Args:
        violations: L1 violations to serialize.

    Returns:
        List of violation payload dictionaries.
    """
    return [{"rule_code": v.rule_code, "rule_name": v.rule_name, "severity": v.severity, "action": v.action, "detail": v.detail} for v in violations]
