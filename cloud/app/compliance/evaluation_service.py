"""Compliance dashboard and evaluation services."""

from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from shared.base_service import BaseService

logger = logging.getLogger(__name__)


class ComplianceEvaluationService(BaseService):
    """Compliance evaluation and dashboard aggregation service."""

    def _connection(self):
        if hasattr(self, "db") and self.db is not None:
            return self.db
        from cloud.app.database import DB_PATH

        self.db = self._connect(DB_PATH)
        return self.db

    def dashboard_summary(self) -> dict[str, Any]:
        db = self.db
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d 00:00:00")
        rows = db.execute("SELECT rule_code, rule_name, visit_data_json, created_at FROM enforcement_log WHERE created_at >= ?", (today,)).fetchall()
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
        try:
            visit_data = json.loads(row["visit_data_json"])
            return visit_data.get("rep_id")
        except (json.JSONDecodeError, TypeError):
            logger.warning("Failed to parse enforcement visit_data_json for dashboard summary", exc_info=True)
            return None

    def dashboard(self) -> dict[str, Any]:
        db = self.db
        today = datetime.now().strftime("%Y-%m-%d")
        w7 = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        tv = db.execute("SELECT COUNT(*) AS c FROM visits WHERE DATE(created_at)=? AND compliance_status!='passed'", (today,)).fetchone()["c"]
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
        rows = self.db.execute(
            "SELECT DATE(created_at) AS d, COUNT(*) AS c FROM visits WHERE created_at >= ? AND compliance_status!='passed' GROUP BY d ORDER BY d",
            (since,),
        ).fetchall()
        return [{"date": (r["d"] or "")[-5:], "count": r["c"]} for r in rows]

    def _top_categories(self) -> list[dict[str, Any]]:
        rows = self.db.execute(
            "SELECT visit_type AS cat, COUNT(*) AS c FROM visits WHERE compliance_status!='passed' GROUP BY visit_type ORDER BY c DESC LIMIT 5"
        ).fetchall()
        total = sum(r["c"] for r in rows) or 1
        return [{"category": r["cat"] or "unknown", "count": r["c"], "percentage": round(r["c"] / total * 100, 1)} for r in rows]

    def _top_reps(self) -> list[dict[str, Any]]:
        rows = self.db.execute(
            "SELECT hcp_name, COUNT(*) AS c FROM visits WHERE compliance_status!='passed' GROUP BY hcp_name ORDER BY c DESC LIMIT 5"
        ).fetchall()
        return [{"repName": r["hcp_name"], "violationCount": r["c"]} for r in rows]
