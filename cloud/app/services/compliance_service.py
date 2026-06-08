"""合规管理服务，提供合规规则 CRUD、仪表盘统计与违规查询功能。"""

import json
import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import ComplianceRulesRepository
from cloud.app.services.base import BaseService

logger = logging.getLogger(__name__)


class ComplianceService(BaseService):
    """合规服务，负责规则的增删查及违规仪表盘数据聚合。"""

    def create_rule(
        self,
        name: str,
        category: str,
        keyword: str,
        max_value: Optional[float],
        created_by: int,
    ) -> dict:
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

    def list_rules(self) -> list:
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
        repo = ComplianceRulesRepository(self.db)
        row = repo.get_by_id(rule_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Rule not found")
        repo.delete(rule_id)

    def dashboard_summary(self) -> dict:
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

        rep_counter = Counter()
        for r in rows:
            try:
                visit_data = json.loads(r["visit_data_json"])
                rep_id = visit_data.get("rep_id")
                if rep_id is not None:
                    rep_counter[rep_id] += 1
            except (json.JSONDecodeError, TypeError):
                logger.warning("Failed to parse enforcement visit_data_json for dashboard summary", exc_info=True)

        return {
            "total_violations_today": total_today,
            "l1_violations": l1_count,
            "most_common_rule": most_common_rule,
            "violations_by_rep": [{"rep_id": rid, "count": cnt} for rid, cnt in rep_counter.items()],
        }

    def rep_violations(self, rep_id: int) -> dict:
        db = self.db
        rows = db.execute(
            "SELECT id, rule_code, rule_name, severity, action, visit_data_json, created_at FROM enforcement_log ORDER BY id"
        ).fetchall()

        result = []
        for r in rows:
            try:
                visit_data = json.loads(r["visit_data_json"])
                if visit_data.get("rep_id") == rep_id:
                    result.append(
                        {
                            "id": r["id"],
                            "rule_code": r["rule_code"],
                            "rule_name": r["rule_name"],
                            "severity": r["severity"],
                            "action": r["action"],
                            "visit_data": visit_data,
                            "created_at": r["created_at"],
                        }
                    )
            except (json.JSONDecodeError, TypeError):
                logger.warning("Failed to parse enforcement visit_data_json for rep violations", exc_info=True)

        return {"rep_id": rep_id, "violations": result}

    def dashboard(self) -> dict:
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
        dt_rows = db.execute(
            "SELECT DATE(created_at) AS d, COUNT(*) AS c FROM visits WHERE created_at >= ? AND compliance_status!='passed' GROUP BY d ORDER BY d",
            (w7,),
        ).fetchall()
        dt = [{"date": (r["d"] or "")[-5:], "count": r["c"]} for r in dt_rows]
        tc_rows = db.execute(
            "SELECT visit_type AS cat, COUNT(*) AS c FROM visits WHERE compliance_status!='passed' GROUP BY visit_type ORDER BY c DESC LIMIT 5"
        ).fetchall()
        tvc = sum(r["c"] for r in tc_rows) or 1
        tc = [
            {
                "category": r["cat"] or "unknown",
                "count": r["c"],
                "percentage": round(r["c"] / tvc * 100, 1),
            }
            for r in tc_rows
        ]
        tr_rows = db.execute(
            "SELECT hcp_name, COUNT(*) AS c FROM visits WHERE compliance_status!='passed' GROUP BY hcp_name ORDER BY c DESC LIMIT 5"
        ).fetchall()
        tr = [{"repName": r["hcp_name"], "violationCount": r["c"]} for r in tr_rows]
        return {
            "todayViolations": tv,
            "weeklyTotal": wt,
            "processedRate": pr,
            "highRiskCount": hrc,
            "dailyTrend": dt,
            "topCategories": tc,
            "topReps": tr,
        }
