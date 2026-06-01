from typing import Optional
import json
from datetime import datetime, timezone, timedelta

from cloud.rules.loader import (
    load_pharma_rules,
    load_research_rules,
    load_pharma_l2_rules,
    load_research_l2_rules,
)
from cloud.app.services.compliance_enforcer import ComplianceEnforcer


class ComplianceStrategyService:
    def __init__(self, db):
        self.db = db
        self.enforcer = ComplianceEnforcer(db) if db else None
        self._pharma_l2_rules = load_pharma_l2_rules()
        self._research_l2_rules = load_research_l2_rules()
        self._all_l2_rules = self._pharma_l2_rules + self._research_l2_rules
        if db:
            self._ensure_tables()

    def _ensure_tables(self):
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

    def evaluate_visit(self, visit_data: dict) -> dict:
        visit_data = visit_data or {}

        l1_violations = self.enforcer.check_visit(visit_data) if self.enforcer else []
        if l1_violations:
            return {
                "level": "L1",
                "action": "block",
                "violations": [
                    {"rule_code": v.rule_code, "rule_name": v.rule_name,
                     "severity": v.severity, "action": v.action, "detail": v.detail}
                    for v in l1_violations
                ],
            }

        l2_violations = self._check_l2_rules(visit_data)
        if l2_violations:
            self._log_l2(l2_violations, visit_data)
            return {"level": "L2", "action": "warn", "violations": l2_violations}

        self._log_l3(visit_data)
        return {"level": "L3", "action": "log", "violations": []}

    def _check_l2_rules(self, visit_data: dict) -> list:
        violations = []
        for rule in self._all_l2_rules:
            v = self._match_l2_rule(rule, visit_data)
            if v:
                violations.append(v)
        return violations

    def _match_l2_rule(self, rule: dict, visit_data: dict) -> Optional[dict]:
        check_type = rule.get("check_type")
        condition = rule.get("condition", {})
        threshold = rule.get("threshold")

        if check_type == "value_threshold":
            return self._check_value_threshold(rule, condition, threshold, visit_data)

        if check_type == "flag_check":
            return self._check_flag(rule, condition, visit_data)

        if check_type == "frequency_count":
            return self._check_frequency(rule, condition, threshold, visit_data)

        if check_type == "concentration_check":
            return self._check_concentration(rule, condition, threshold, visit_data)

        if check_type == "citation_check":
            return self._check_citation(rule, condition, visit_data)

        if check_type == "expiry_check":
            return self._check_expiry(rule, condition, threshold, visit_data)

        if check_type == "discount_check":
            return self._check_discount(rule, condition, threshold, visit_data)

        return None

    def _check_value_threshold(self, rule, condition, threshold, visit_data):
        field = condition.get("field")
        op = condition.get("operator", "gt")
        field_val = visit_data.get(field)
        try:
            val = float(field_val) if field_val is not None else 0
            thr = float(threshold)
            if (op == "gt" and val > thr) or (op == "gte" and val >= thr) \
               or (op == "lt" and val < thr) or (op == "lte" and val <= thr) \
               or (op == "eq" and val == thr):
                return self._l2_violation(rule, f"字段[{field}]值[{val}]超出阈值[{thr}]")
        except (TypeError, ValueError):
            pass
        return None

    def _check_flag(self, rule, condition, visit_data):
        field = condition.get("field")
        expected = condition.get("expected")
        if visit_data.get(field) != expected:
            return self._l2_violation(rule, f"字段[{field}]期望值[{expected}]，实际值[{visit_data.get(field)}]")
        return None

    def _check_frequency(self, rule, condition, threshold, visit_data):
        field = condition.get("field")
        window_days = condition.get("window_days", 7)
        entity_id = visit_data.get(field)
        if entity_id is None:
            return None
        since = (datetime.now() - timedelta(days=window_days)).isoformat()
        count = self.db.execute(
            f"SELECT COUNT(*) AS c FROM visits WHERE {field} = ? AND created_at >= ?",
            (entity_id, since),
        ).fetchone()["c"]
        if count >= int(threshold):
            return self._l2_violation(rule, f"实体[{entity_id}]在{window_days}天内拜访{count}次，阈值[{threshold}]")
        return None

    def _check_concentration(self, rule, condition, threshold, visit_data):
        field = condition.get("field")
        ratio_threshold = condition.get("ratio_threshold", 0.8)
        window_days = condition.get("window_days", 30)
        dept_val = visit_data.get(field)
        if dept_val is None:
            return None
        since = (datetime.now() - timedelta(days=window_days)).isoformat()
        total = self.db.execute(
            "SELECT COUNT(*) AS c FROM visits WHERE created_at >= ?", (since,)
        ).fetchone()["c"]
        if total > 0:
            dept_count = self.db.execute(
                f"SELECT COUNT(*) AS c FROM visits WHERE {field} = ? AND created_at >= ?",
                (dept_val, since),
            ).fetchone()["c"]
            ratio = dept_count / total
            if ratio >= ratio_threshold:
                return self._l2_violation(rule, f"值[{dept_val}]占比{ratio:.1%}，阈值[{ratio_threshold:.0%}]")
        return None

    def _check_citation(self, rule, condition, visit_data):
        field = condition.get("field")
        expected = condition.get("expected")
        if visit_data.get(field) != expected:
            return self._l2_violation(rule, f"引用未验证，字段[{field}]值[{visit_data.get(field)}]")
        return None

    def _check_expiry(self, rule, condition, threshold, visit_data):
        field = condition.get("field")
        lead_days = condition.get("lead_days", 90)
        expiry = visit_data.get(field)
        if expiry:
            try:
                expiry_date = datetime.fromisoformat(expiry) if isinstance(expiry, str) else expiry
                if isinstance(expiry_date, datetime):
                    remaining = (expiry_date - datetime.now()).days
                    if remaining <= lead_days:
                        return self._l2_violation(rule, f"资质{remaining}天后到期，预警期{lead_days}天")
            except (ValueError, TypeError):
                pass
        return None

    def _check_discount(self, rule, condition, threshold, visit_data):
        field = condition.get("field")
        op = condition.get("operator", "lt")
        field_val = visit_data.get(field)
        try:
            val = float(field_val) if field_val is not None else 1.0
            thr = float(threshold)
            if op == "lt" and val < thr:
                return self._l2_violation(rule, f"折扣率{val:.0%}低于阈值{thr:.0%}")
            if op == "gt" and val > thr:
                return self._l2_violation(rule, f"折扣率{val:.0%}超过阈值{thr:.0%}")
        except (TypeError, ValueError):
            pass
        return None

    def _l2_violation(self, rule, detail=""):
        return {
            "rule_id": rule.get("id"),
            "rule_name": rule.get("name"),
            "severity": rule.get("severity"),
            "check_type": rule.get("check_type"),
            "detail": f"L2规则'{rule.get('id')}'触发: {rule.get('name')}. {detail}",
        }

    def _log_l2(self, violations, visit_data):
        now = datetime.now(timezone.utc).isoformat()
        for v in violations:
            self.db.execute(
                "INSERT INTO compliance_l2_log (rule_id, rule_name, severity, check_type, visit_data_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (v["rule_id"], v["rule_name"], v["severity"], v["check_type"], json.dumps(visit_data, ensure_ascii=False), now),
            )
        self.db.commit()

    def _log_l3(self, visit_data):
        now = datetime.now(timezone.utc).isoformat()
        self.db.execute(
            "INSERT INTO compliance_l3_log (visit_data_json, created_at) VALUES (?, ?)",
            (json.dumps(visit_data, ensure_ascii=False), now),
        )
        self.db.commit()

    def get_strategy(self, rule_id: str) -> Optional[dict]:
        for rule in load_pharma_rules():
            if rule.get("code") == rule_id:
                return {"rule_id": rule_id, "level": "L1", "action": "block", "severity": rule.get("severity")}
        for rule in load_research_rules():
            if rule.get("code") == rule_id:
                return {"rule_id": rule_id, "level": "L1", "action": "block", "severity": rule.get("severity")}
        for rule in self._all_l2_rules:
            if rule.get("id") == rule_id:
                sev = rule.get("severity")
                action = "warn" if sev in ("warning",) else "review"
                return {"rule_id": rule_id, "level": "L2", "action": action, "severity": sev}
        return None

    def get_l2_rules(self) -> list:
        return self._all_l2_rules
