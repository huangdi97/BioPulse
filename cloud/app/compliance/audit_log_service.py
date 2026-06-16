"""Compliance audit log and violation tracking service."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from shared.base_service import BaseService

logger = logging.getLogger(__name__)


class ComplianceAuditLogService(BaseService):
    """Compliance audit log service for rep violation queries."""

    def _connection(self):
        if hasattr(self, "db") and self.db is not None:
            return self.db
        from cloud.app.database import DB_PATH

        self.db = self._connect(DB_PATH)
        return self.db

    def rep_violations(self, rep_id: int) -> dict[str, Any]:
        """Return violations for one representative.

        Args:
            rep_id: Representative id to filter by.

        Returns:
            Representative violation payload.
        """
        db = self._connection()
        rows = db.execute(
            "SELECT id, rule_code, rule_name, severity, action, visit_data_json, created_at FROM enforcement_log ORDER BY id"
        ).fetchall()

        result = []
        for row in rows:
            violation = self._violation_for_rep(row, rep_id)
            if violation:
                result.append(violation)

        return {"rep_id": rep_id, "violations": result}

    def _violation_for_rep(self, row: Any, rep_id: int) -> Optional[dict[str, Any]]:
        """Build a violation payload when a row belongs to a representative.

        Args:
            row: SQLite row containing violation and visit data.
            rep_id: Representative id to match.

        Returns:
            Violation payload or None when the row does not match.
        """
        try:
            visit_data = json.loads(row["visit_data_json"])
        except (json.JSONDecodeError, TypeError):
            logger.warning("Failed to parse enforcement visit_data_json for rep violations", exc_info=True)
            return None
        if visit_data.get("rep_id") != rep_id:
            return None
        return {
            "id": row["id"],
            "rule_code": row["rule_code"],
            "rule_name": row["rule_name"],
            "severity": row["severity"],
            "action": row["action"],
            "visit_data": visit_data,
            "created_at": row["created_at"],
        }
