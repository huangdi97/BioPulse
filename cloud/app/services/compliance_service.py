from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import ComplianceRulesRepository
from cloud.app.services.base import BaseService


class ComplianceService(BaseService):
    def create_rule(self, name: str, category: str, keyword: str, max_value: Optional[float], created_by: int) -> dict:
        repo = ComplianceRulesRepository(self.db)
        row_id = repo.create({"name": name, "category": category, "keyword": keyword, "max_value": max_value, "created_by": created_by})
        return {"id": row_id, "name": name, "category": category, "keyword": keyword, "max_value": max_value}

    def list_rules(self) -> list:
        repo = ComplianceRulesRepository(self.db)
        return [{"id": r["id"], "name": r["name"], "category": r["category"], "keyword": r["keyword"], "max_value": r["max_value"]} for r in repo.list_all()]

    def delete_rule(self, rule_id: int) -> None:
        repo = ComplianceRulesRepository(self.db)
        row = repo.get_by_id(rule_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Rule not found")
        repo.delete(rule_id)

    def dashboard(self) -> dict:
        db = self.db
        today = datetime.now().strftime("%Y-%m-%d")
        w7 = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        tv = db.execute(
            "SELECT COUNT(*) AS c FROM visits WHERE DATE(created_at)=? AND compliance_status!='passed'",
            (today,)).fetchone()["c"]
        wt = db.execute(
            "SELECT COUNT(*) AS c FROM visits WHERE created_at >= ?",
            (w7,)).fetchone()["c"]
        total = db.execute("SELECT COUNT(*) AS c FROM visits").fetchone()["c"]
        processed = db.execute(
            "SELECT COUNT(*) AS c FROM visits WHERE compliance_status IS NOT NULL AND compliance_status!=''"
        ).fetchone()["c"]
        pr = round(processed / total * 100, 1) if total else 0.0
        hrc = db.execute(
            "SELECT COUNT(*) AS c FROM visits WHERE compliance_status='critical'"
        ).fetchone()["c"]
        dt_rows = db.execute(
            "SELECT DATE(created_at) AS d, COUNT(*) AS c FROM visits "
            "WHERE created_at >= ? AND compliance_status!='passed' "
            "GROUP BY d ORDER BY d", (w7,)).fetchall()
        dt = [{"date": (r["d"] or "")[-5:], "count": r["c"]} for r in dt_rows]
        tc_rows = db.execute(
            "SELECT visit_type AS cat, COUNT(*) AS c FROM visits "
            "WHERE compliance_status!='passed' "
            "GROUP BY visit_type ORDER BY c DESC LIMIT 5").fetchall()
        tvc = sum(r["c"] for r in tc_rows) or 1
        tc = [{"category": r["cat"] or "unknown", "count": r["c"], "percentage": round(r["c"] / tvc * 100, 1)} for r in tc_rows]
        tr_rows = db.execute(
            "SELECT hcp_name, COUNT(*) AS c FROM visits "
            "WHERE compliance_status!='passed' "
            "GROUP BY hcp_name ORDER BY c DESC LIMIT 5").fetchall()
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
