"""Tests for cloud.app.compliance.engine.ComplianceEngine."""

import sqlite3

from cloud.app.compliance.engine import ComplianceEngine


class TestComplianceEngine:
    def _make_engine(self) -> ComplianceEngine:
        db = sqlite3.connect(":memory:")
        return ComplianceEngine(db)

    def _pass_visit(self) -> dict:
        return {
            "scope": "pharma",
            "rep_id": "R001",
            "notes": "正常拜访，学术交流",
            "promotion_content": "产品介绍",
            "expense_notes": "交通费",
            "non_compete_waived": True,
            "location_type": "hospital",
            "expenses": 100,
        }

    def test_check_visit_basic(self):
        engine = self._make_engine()
        violations = engine.check_visit(self._pass_visit())
        assert len(violations) == 0, f"Expected L1 pass, got violations: {violations}"

    def test_check_visit_blocked(self):
        engine = self._make_engine()
        data = self._pass_visit()
        data["expenses"] = 500
        violations = engine.check_visit(data)
        assert len(violations) > 0, "Expected L1 violations"
        codes = [v.rule_code for v in violations]
        assert "PHR-L1-003" in codes, "Expected PHR-L1-003 (利益输送拦截)"

    def test_check_visit_l2(self):
        engine = self._make_engine()
        engine.db.execute("CREATE TABLE IF NOT EXISTS visits (id INTEGER PRIMARY KEY, rep_id TEXT, hcp_id TEXT, created_at TEXT)")
        engine.db.commit()
        data = self._pass_visit()
        assert len(engine.check_visit(data)) == 0
        data["meeting_registered"] = False
        l2_results = engine.check_visit_l2(data)
        assert len(l2_results) > 0, "Expected L2 violations"
        ids = [r["rule_id"] for r in l2_results]
        assert "PHR-L2-003" in ids, "Expected PHR-L2-003 (会议参与合规)"
