"""Compliance rule CRUD and dashboard service."""

from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import ComplianceRulesRepository
from shared.base_service import BaseService

logger = logging.getLogger(__name__)


class ComplianceService(BaseService):
    """Compliance management service for rules and dashboard aggregation."""

    def create_rule(
        self,
        name: str,
        category: str,
        keyword: str,
        max_value: Optional[float],
        created_by: int,
    ) -> dict[str, Any]:
        """Create a compliance rule.

        Args:
            name: Rule display name.
            category: Rule category.
            keyword: Keyword used by the rule.
            max_value: Optional numeric threshold.
            created_by: User id that creates the rule.

        Returns:
            Created rule payload.
        """
        repo = ComplianceRulesRepository(self.db)
        row_id = repo.create(
            {
                "name": name,
                "category": category,
                "keyword": keyword,
                "max_value": max_value,
                "created_by": created_by,
            }
        )
        return {
            "id": row_id,
            "name": name,
            "category": category,
            "keyword": keyword,
            "max_value": max_value,
        }

    def list_rules(self) -> list[dict[str, Any]]:
        """List all compliance rules.

        Args:
            None.

        Returns:
            List of compliance rule payloads.
        """
        repo = ComplianceRulesRepository(self.db)
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "category": r["category"],
                "keyword": r["keyword"],
                "max_value": r["max_value"],
            }
            for r in repo.list_all()
        ]

    def delete_rule(self, rule_id: int) -> None:
        """Delete a compliance rule.

        Args:
            rule_id: Rule id to delete.

        Returns:
            None.
        """
        repo = ComplianceRulesRepository(self.db)
        row = repo.get_by_id(rule_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Rule not found")
        repo.delete(rule_id)

    def dashboard_summary(self) -> dict[str, Any]:
        """Return today's violation summary.

        Args:
            None.

        Returns:
            Dashboard summary payload.
        """
        db = self.db
        today = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00")
        rows = db.execute(
            "SELECT rule_code, rule_name, visit_data_json, created_at FROM enforcement_log WHERE created_at >= ?",
            (today,),
        ).fetchall()

        total_today = len(rows)
        l1_count = len([r for r in rows if "L1" in r["rule_code"]])
        rule_counter = Counter(r["rule_code"] for r in rows)
        most_common = rule_counter.most_common(1)
        most_common_rule = most_common[0][0] if most_common else ""

        rep_counter: Counter[Any] = Counter()
        for row in rows:
            rep_id = self._rep_id_from_row(row)
            if rep_id is not None:
                rep_counter[rep_id] += 1

        return {
            "total_violations_today": total_today,
            "l1_violations": l1_count,
            "most_common_rule": most_common_rule,
            "violations_by_rep": [{"rep_id": rid, "count": cnt} for rid, cnt in rep_counter.items()],
        }

    def _rep_id_from_row(self, row: Any) -> Any:
        """Extract representative id from an enforcement row.

        Args:
            row: SQLite row containing visit_data_json.

        Returns:
            Representative id or None when unavailable.
        """
        try:
            visit_data = json.loads(row["visit_data_json"])
            return visit_data.get("rep_id")
        except (json.JSONDecodeError, TypeError):
            logger.warning("Failed to parse enforcement visit_data_json for dashboard summary", exc_info=True)
            return None

    def rep_violations(self, rep_id: int) -> dict[str, Any]:
        """Return violations for one representative.

        Args:
            rep_id: Representative id to filter by.

        Returns:
            Representative violation payload.
        """
        db = self.db
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

    def dashboard(self) -> dict[str, Any]:
        """Return compliance dashboard metrics.

        Args:
            None.

        Returns:
            Dashboard metrics payload.
        """
        db = self.db
        today = datetime.now().strftime("%Y-%m-%d")
        w7 = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        tv = db.execute(
            "SELECT COUNT(*) AS c FROM visits WHERE DATE(created_at)=? AND compliance_status!='passed'",
            (today,),
        ).fetchone()["c"]
        wt = db.execute("SELECT COUNT(*) AS c FROM visits WHERE created_at >= ?", (w7,)).fetchone()["c"]
        total = db.execute("SELECT COUNT(*) AS c FROM visits").fetchone()["c"]
        processed = db.execute("SELECT COUNT(*) AS c FROM visits WHERE compliance_status IS NOT NULL AND compliance_status!=''").fetchone()["c"]
        pr = round(processed / total * 100, 1) if total else 0.0
        hrc = db.execute("SELECT COUNT(*) AS c FROM visits WHERE compliance_status='critical'").fetchone()["c"]
        dt = self._daily_trend(w7)
        tc = self._top_categories()
        tr = self._top_reps()
        return {
            "todayViolations": tv,
            "weeklyTotal": wt,
            "processedRate": pr,
            "highRiskCount": hrc,
            "dailyTrend": dt,
            "topCategories": tc,
            "topReps": tr,
        }

    def _daily_trend(self, since: str) -> list[dict[str, Any]]:
        """Return daily violation trend rows.

        Args:
            since: Lower-bound created_at timestamp.

        Returns:
            Daily trend payload list.
        """
        rows = self.db.execute(
            "SELECT DATE(created_at) AS d, COUNT(*) AS c FROM visits WHERE created_at >= ? AND compliance_status!='passed' GROUP BY d ORDER BY d",
            (since,),
        ).fetchall()
        return [{"date": (r["d"] or "")[-5:], "count": r["c"]} for r in rows]

    def _top_categories(self) -> list[dict[str, Any]]:
        """Return top violating visit categories.

        Args:
            None.

        Returns:
            Category summary payload list.
        """
        rows = self.db.execute(
            "SELECT visit_type AS cat, COUNT(*) AS c FROM visits WHERE compliance_status!='passed' GROUP BY visit_type ORDER BY c DESC LIMIT 5"
        ).fetchall()
        total = sum(r["c"] for r in rows) or 1
        return [{"category": r["cat"] or "unknown", "count": r["c"], "percentage": round(r["c"] / total * 100, 1)} for r in rows]

    def _top_reps(self) -> list[dict[str, Any]]:
        """Return top representatives by violation count.

        Args:
            None.

        Returns:
            Representative summary payload list.
        """
        rows = self.db.execute(
            "SELECT hcp_name, COUNT(*) AS c FROM visits WHERE compliance_status!='passed' GROUP BY hcp_name ORDER BY c DESC LIMIT 5"
        ).fetchall()
        return [{"repName": r["hcp_name"], "violationCount": r["c"]} for r in rows]
