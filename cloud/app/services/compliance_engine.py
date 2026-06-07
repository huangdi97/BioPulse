import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from cloud.rules.loader import load_pharma_l2_rules, load_pharma_rules, load_research_l2_rules, load_research_rules


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _float(value) -> Optional[float]:
    try:
        return float(value) if value is not None else 0.0
    except (TypeError, ValueError):
        return None


def _count(row) -> int:
    return row["c"] if hasattr(row, "keys") and "c" in row.keys() else row[0]


@dataclass
class Violation:
    rule_code: str
    rule_name: str
    severity: str
    action: str
    detail: str


@dataclass
class DetectionRule:
    code: str
    name: str
    level: str
    action: str
    severity: str
    detection_type: str
    detection_field: str
    operator: str
    value: object
    keywords: list = field(default_factory=list)
    exclude_when: dict = field(default_factory=dict)


class EnforcerEngine:
    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self._rules = load_pharma_rules()
        self._parsed_rules = [self._parse_rule(rule) for rule in self._rules]
        self._l2_rules = load_pharma_l2_rules() + load_research_l2_rules()

    def _parse_rule(self, rule: dict) -> DetectionRule:
        detection = rule.get("detection", {})
        return DetectionRule(
            rule.get("code", ""),
            rule.get("name", ""),
            rule.get("level", ""),
            rule.get("action", ""),
            rule.get("severity", ""),
            detection.get("type", ""),
            detection.get("field", ""),
            detection.get("operator", ""),
            detection.get("value", ""),
            detection.get("keywords", []),
            detection.get("exclude_when", {}),
        )

    def check_visit(self, visit_data: dict) -> list[Violation]:
        data = visit_data or {}
        data["notes"] = (data.get("notes") or "")[:5000]
        data["expenses"] = max(0, data.get("expenses") or 0)
        return [v for rule in self._parsed_rules if rule.level == "L1" for v in [self._match_l1(rule, data)] if v]

    def _match_l1(self, rule: DetectionRule, data: dict) -> Optional[Violation]:
        value = data.get(rule.detection_field)
        exclude = rule.exclude_when
        if exclude and exclude.get("operator") == "eq" and data.get(exclude.get("field")) == exclude.get("value"):
            return None
        if rule.detection_type == "keyword_match" and value and any(keyword in str(value) for keyword in rule.keywords):
            return self._l1_violation(rule)
        if rule.detection_type == "threshold" and self._compare(value, rule.operator, rule.value):
            return self._l1_violation(rule)
        if rule.detection_type == "field_check":
            matched = (rule.operator == "eq" and value == rule.value) or (rule.operator == "neq" and value != rule.value)
            return self._l1_violation(rule) if matched else None
        return None

    def _compare(self, value, operator: str, threshold) -> bool:
        current = _float(value)
        expected = _float(threshold)
        if current is None or expected is None:
            return False
        return {
            "gt": current > expected,
            "gte": current >= expected,
            "lt": current < expected,
            "lte": current <= expected,
            "eq": current == expected,
        }.get(operator, False)

    def _l1_violation(self, rule: DetectionRule) -> Violation:
        return Violation(rule.code, rule.name, rule.severity, rule.action, f"Rule '{rule.code}' triggered: {rule.name}")

    def get_l1_rules(self) -> list:
        return [rule for rule in self._parsed_rules if rule.level == "L1"]

    def get_l2_rules(self) -> list:
        return self._l2_rules

    def check_visit_l2(self, visit_data: dict) -> list:
        return self.check_l2_rules(self._l2_rules, visit_data or {})

    def check_l2_rules(self, rules: list, visit_data: dict) -> list:
        return [v for rule in rules for v in [self._match_l2(rule, visit_data or {})] if v]

    def _match_l2(self, rule: dict, data: dict) -> Optional[dict]:
        check_type = rule.get("check_type")
        condition = rule.get("condition", {})
        threshold = rule.get("threshold")
        if check_type == "value_threshold":
            field = condition.get("field")
            value, expected = _float(data.get(field)), _float(threshold)
            if value is not None and expected is not None and self._compare(value, condition.get("operator", "gt"), expected):
                return self._l2_violation(rule, f"字段[{field}]值[{value}]超出阈值[{expected}]")
        if check_type == "flag_check":
            field = condition.get("field")
            expected = condition.get("expected")
            if data.get(field) != expected:
                return self._l2_violation(rule, f"字段[{field}]期望值[{expected}]，实际值[{data.get(field)}]")
        if check_type == "frequency_count":
            field = condition.get("field")
            entity_id = data.get(field)
            if entity_id is not None:
                window_days = condition.get("window_days", 7)
                since = (datetime.now() - timedelta(days=window_days)).isoformat()
                count = _count(
                    self.db.execute(f"SELECT COUNT(*) AS c FROM visits WHERE {field} = ? AND created_at >= ?", (entity_id, since)).fetchone()
                )
                if count >= int(threshold):
                    return self._l2_violation(rule, f"实体[{entity_id}]在{window_days}天内拜访{count}次，阈值[{threshold}]")
        if check_type == "concentration_check":
            field = condition.get("field")
            value = data.get(field)
            if value is not None:
                window_days = condition.get("window_days", 30)
                since = (datetime.now() - timedelta(days=window_days)).isoformat()
                total = _count(self.db.execute("SELECT COUNT(*) AS c FROM visits WHERE created_at >= ?", (since,)).fetchone())
                if total > 0:
                    matched = _count(
                        self.db.execute(f"SELECT COUNT(*) AS c FROM visits WHERE {field} = ? AND created_at >= ?", (value, since)).fetchone()
                    )
                    ratio = matched / total
                    threshold = condition.get("ratio_threshold", 0.8)
                    if ratio >= threshold:
                        return self._l2_violation(rule, f"值[{value}]占比{ratio:.1%}，阈值[{threshold:.0%}]")
        if check_type == "citation_check":
            field = condition.get("field")
            expected = condition.get("expected")
            if data.get(field) != expected:
                return self._l2_violation(rule, f"引用未验证，字段[{field}]值[{data.get(field)}]")
        if check_type == "expiry_check":
            field = condition.get("field")
            expiry = data.get(field)
            if expiry:
                try:
                    expiry_date = datetime.fromisoformat(expiry) if isinstance(expiry, str) else expiry
                    remaining = (expiry_date - datetime.now()).days if isinstance(expiry_date, datetime) else None
                    lead_days = condition.get("lead_days", 90)
                    if remaining is not None and remaining <= lead_days:
                        return self._l2_violation(rule, f"资质{remaining}天后到期，预警期{lead_days}天")
                except (TypeError, ValueError):
                    pass
        if check_type == "discount_check":
            field = condition.get("field")
            value, expected = _float(data.get(field)), _float(threshold)
            value = 1.0 if value is None else value
            operator = condition.get("operator", "lt")
            if expected is not None and operator == "lt" and value < expected:
                return self._l2_violation(rule, f"折扣率{value:.0%}低于阈值{expected:.0%}")
            if expected is not None and operator == "gt" and value > expected:
                return self._l2_violation(rule, f"折扣率{value:.0%}超过阈值{expected:.0%}")
        return None

    def _l2_violation(self, rule: dict, detail: str) -> dict:
        return {
            "rule_id": rule.get("id"),
            "rule_name": rule.get("name"),
            "severity": rule.get("severity"),
            "check_type": rule.get("check_type"),
            "detail": f"L2规则'{rule.get('id')}'触发: {rule.get('name')}. {detail}",
        }


class EnforcerAudit:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def _ensure_table(self):
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS enforcement_log (id INTEGER PRIMARY KEY AUTOINCREMENT, rule_code TEXT NOT NULL, rule_name TEXT NOT NULL, severity TEXT NOT NULL, action TEXT NOT NULL, visit_data_json TEXT NOT NULL, created_at TEXT NOT NULL)"
        )
        self.db.commit()

    def _ensure_l2_tables(self):
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS compliance_l2_log (id INTEGER PRIMARY KEY AUTOINCREMENT, rule_id TEXT NOT NULL, rule_name TEXT NOT NULL, severity TEXT NOT NULL, check_type TEXT NOT NULL, visit_data_json TEXT NOT NULL, created_at TEXT NOT NULL)"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS compliance_l3_log (id INTEGER PRIMARY KEY AUTOINCREMENT, visit_data_json TEXT NOT NULL, created_at TEXT NOT NULL)"
        )
        self.db.commit()

    def ensure_tables(self):
        self._ensure_table()
        self._ensure_l2_tables()

    def _log_violation(self, violation, visit_data: dict):
        self.db.execute(
            "INSERT INTO enforcement_log (rule_code, rule_name, severity, action, visit_data_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (violation.rule_code, violation.rule_name, violation.severity, violation.action, json.dumps(visit_data, ensure_ascii=False), _now()),
        )
        self.db.commit()

    def _log_l2_batch(self, violations: list, visit_data: dict):
        payload, now = json.dumps(visit_data, ensure_ascii=False), _now()
        for violation in violations:
            self.db.execute(
                "INSERT INTO compliance_l2_log (rule_id, rule_name, severity, check_type, visit_data_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (violation["rule_id"], violation["rule_name"], violation["severity"], violation["check_type"], payload, now),
            )
        self.db.commit()

    def _log_l3(self, visit_data: dict):
        self.db.execute(
            "INSERT INTO compliance_l3_log (visit_data_json, created_at) VALUES (?, ?)", (json.dumps(visit_data, ensure_ascii=False), _now())
        )
        self.db.commit()


def _l1_payload(violations: list[Violation]) -> list[dict]:
    return [{"rule_code": v.rule_code, "rule_name": v.rule_name, "severity": v.severity, "action": v.action, "detail": v.detail} for v in violations]


class ComplianceEnforcer:
    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self._engine = EnforcerEngine(db)
        self._audit = EnforcerAudit(db)
        self._audit.ensure_tables()

    def check_visit(self, visit_data: dict) -> list[Violation]:
        violations = self._engine.check_visit(visit_data)
        for violation in violations:
            self._audit._log_violation(violation, visit_data)
        return violations

    def get_l1_rules(self) -> list:
        return self._engine.get_l1_rules()

    def get_l2_rules(self) -> list:
        return self._engine.get_l2_rules()

    def check_all_levels(self, visit_data: dict) -> dict:
        data = visit_data or {}
        l1 = self.check_visit(data)
        if l1:
            return {"level": "L1", "action": "block", "violations": _l1_payload(l1)}
        l2 = self.check_visit_l2(data)
        if l2:
            self._audit._log_l2_batch(l2, data)
            return {"level": "L2", "action": "warn", "violations": l2}
        self._audit._log_l3(data)
        return {"level": "L3", "action": "log", "violations": []}

    def check_visit_l2(self, visit_data: dict) -> list:
        return self._engine.check_visit_l2(visit_data)


class ResearchComplianceEnforcer:
    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self._rules = load_research_rules()
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS research_enforcement_log (id INTEGER PRIMARY KEY AUTOINCREMENT, rule_code TEXT NOT NULL, rule_name TEXT NOT NULL, severity TEXT NOT NULL, action TEXT NOT NULL, visit_data_json TEXT NOT NULL, created_at TEXT NOT NULL)"
        )
        self.db.commit()

    def check_research_visit(self, visit_data: dict) -> list[Violation]:
        violations = []
        for rule in self._rules:
            if rule.get("level") != "L1":
                continue
            violation = Violation(
                rule["code"],
                rule["name"],
                rule.get("severity", "critical"),
                rule.get("action", "block"),
                f"Research rule '{rule['code']}' triggered: {rule['name']}",
            )
            violations.append(violation)
            self.db.execute(
                "INSERT INTO research_enforcement_log (rule_code, rule_name, severity, action, visit_data_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (violation.rule_code, violation.rule_name, violation.severity, violation.action, json.dumps(visit_data, ensure_ascii=False), _now()),
            )
            self.db.commit()
        return violations

    def get_l1_rules(self) -> list:
        return [rule for rule in self._rules if rule.get("level") == "L1"]


class ComplianceStrategyService:
    def __init__(self, db):
        self.db = db
        self.enforcer = ComplianceEnforcer(db) if db else None
        self._all_l2_rules = load_pharma_l2_rules() + load_research_l2_rules()
        if db:
            EnforcerAudit(db)._ensure_l2_tables()

    def evaluate_visit(self, visit_data: dict) -> dict:
        if self.enforcer:
            return self.enforcer.check_all_levels(visit_data)
        return {"level": "L3", "action": "log", "violations": []}

    def _check_l2_rules(self, visit_data: dict) -> list:
        return EnforcerEngine(self.db).check_l2_rules(self._all_l2_rules, visit_data)

    def _match_l2_rule(self, rule: dict, visit_data: dict) -> Optional[dict]:
        return EnforcerEngine(self.db)._match_l2(rule, visit_data)

    def _log_l2(self, violations, visit_data):
        EnforcerAudit(self.db)._log_l2_batch(violations, visit_data)

    def _log_l3(self, visit_data):
        EnforcerAudit(self.db)._log_l3(visit_data)

    def get_strategy(self, rule_id: str) -> Optional[dict]:
        for rules in (load_pharma_rules(), load_research_rules()):
            for rule in rules:
                if rule.get("code") == rule_id:
                    return {"rule_id": rule_id, "level": "L1", "action": "block", "severity": rule.get("severity")}
        for rule in self._all_l2_rules:
            if rule.get("id") == rule_id:
                severity = rule.get("severity")
                return {"rule_id": rule_id, "level": "L2", "action": "warn" if severity in ("warning",) else "review", "severity": severity}
        return None

    def get_l2_rules(self) -> list:
        return self._all_l2_rules
