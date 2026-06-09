"""Manage compliance rule loading, evaluation, and violation reporting."""

import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from cloud.rules.loader import load_pharma_l2_rules, load_pharma_rules, load_research_l2_rules

logger = logging.getLogger(__name__)


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
        """初始化合规规则引擎，加载 L1 和 L2 规则集。"""
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
        """对拜访数据执行所有 L1 硬阻断规则匹配，返回违规列表。"""
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
        """获取当前已解析的 L1 硬阻断规则列表。"""
        return [rule for rule in self._parsed_rules if rule.level == "L1"]

    def get_l2_rules(self) -> list:
        """获取当前 L2 软告警规则列表。"""
        return self._l2_rules

    def check_visit_l2(self, visit_data: dict) -> list:
        """对拜访数据执行所有 L2 软告警规则匹配。"""
        return self.check_l2_rules(self._l2_rules, visit_data or {})

    def check_l2_rules(self, rules: list, visit_data: dict) -> list:
        """对拜访数据执行自定义 L2 规则列表匹配，返回违规详情。"""
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
                    logger.warning("Failed to parse expiry date for L2 compliance rule", exc_info=True)
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
