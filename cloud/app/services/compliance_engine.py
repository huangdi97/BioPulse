"""合规引擎模块，实现医药拜访合规校验的L1硬阻断、L2软告警、L3全量审计三级策略架构。依赖json、sqlite3、compliance_logger与compliance_rules等外部模块。"""

import json
import sqlite3
from typing import Optional

from cloud.app.services.compliance_logger import EnforcerAudit, _l1_payload
from cloud.app.services.compliance_rules import EnforcerEngine, Violation, _now
from cloud.rules.loader import load_pharma_l2_rules, load_pharma_rules, load_research_l2_rules, load_research_rules


class ComplianceEngine:
    def __init__(self, db: sqlite3.Connection):
        """初始化合规引擎，绑定数据库连接与审计日志器。"""
        self.db = db
        self._engine = EnforcerEngine(db)
        self._audit = EnforcerAudit(db)
        self._audit.ensure_tables()

    def check_visit(self, visit_data: dict) -> list[Violation]:
        """对拜访数据执行 L1 硬阻断合规检查。"""
        violations = self._engine.check_visit(visit_data)
        for violation in violations:
            self._audit._log_violation(violation, visit_data)
        return violations

    def get_l1_rules(self) -> list:
        """获取当前 L1 硬阻断规则列表。"""
        return self._engine.get_l1_rules()

    def get_l2_rules(self) -> list:
        """获取当前 L2 软告警规则列表。"""
        return self._engine.get_l2_rules()

    def check_all_levels(self, visit_data: dict) -> dict:
        """执行三级合规检查（L1 阻断 → L2 告警 → L3 审计），返回分级结果。"""
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
        """对拜访数据执行 L2 软告警合规检查。"""
        return self._engine.check_visit_l2(visit_data)


ComplianceEnforcer = ComplianceEngine


class ResearchComplianceEnforcer:
    def __init__(self, db: sqlite3.Connection):
        """初始化科研模式合规执行器，加载科研规则并创建日志表。"""
        self.db = db
        self._rules = load_research_rules()
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS research_enforcement_log (id INTEGER PRIMARY KEY AUTOINCREMENT, rule_code TEXT NOT NULL, rule_name TEXT NOT NULL, severity TEXT NOT NULL, action TEXT NOT NULL, visit_data_json TEXT NOT NULL, created_at TEXT NOT NULL)"
        )
        self.db.commit()

    def check_research_visit(self, visit_data: dict) -> list[Violation]:
        """对科研拜访数据执行 L1 规则检查并记录违规日志。"""
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
        """获取科研模式的 L1 硬阻断规则。"""
        return [rule for rule in self._rules if rule.get("level") == "L1"]


class ComplianceStrategyService:
    def __init__(self, db):
        """初始化合规策略服务，加载 L1 和 L2 规则集。"""
        self.db = db
        self.enforcer = ComplianceEnforcer(db) if db else None
        self._all_l2_rules = load_pharma_l2_rules() + load_research_l2_rules()
        if db:
            EnforcerAudit(db)._ensure_l2_tables()

    def evaluate_visit(self, visit_data: dict) -> dict:
        """评估一次拜访数据的全量合规风险（三级联动）。"""
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
        """根据规则 ID 获取合规策略详情与处理建议。"""
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
        """获取全部 L2 软告警规则列表。"""
        return self._all_l2_rules
