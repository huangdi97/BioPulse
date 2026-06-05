"""Compliance audit logging — table creation and violation persistence."""

import json
import sqlite3
from datetime import datetime, timezone


class EnforcerAudit:
    """Audit logging for compliance violations — no detection logic."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db

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

    def _log_violation(self, violation, visit_data: dict):
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

    def ensure_tables(self):
        self._ensure_table()
        self._ensure_l2_tables()

    def _log_l2_batch(self, violations: list, visit_data: dict):
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        for v in violations:
            self.db.execute(
                "INSERT INTO compliance_l2_log (rule_id, rule_name, severity, check_type, visit_data_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    v["rule_id"],
                    v["rule_name"],
                    v["severity"],
                    v["check_type"],
                    json.dumps(visit_data, ensure_ascii=False),
                    now,
                ),
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
