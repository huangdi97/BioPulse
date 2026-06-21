"""统一排除闸模块 — 集中评估所有规则的 exclude_when 条件。

接口: evaluate(context) → (excluded_rules, reason)
"""

from __future__ import annotations

from typing import Any

from cloud.rules.loader import load_pharma_l2_rules, load_pharma_rules, load_research_l2_rules


def evaluate(context: dict[str, Any]) -> tuple[dict[str, str], str]:
    """集中评估所有L1/L2规则的 exclude_when 条件。

    Args:
        context: 上下文，必须包含 "data" 键（待检测数据载荷）。
                 可选 "gate_overrides" 覆盖默认开关行为。

    Returns:
        (excluded_rules, reason)
        excluded_rules: rule_code → reason 映射。
        reason: 汇总原因，无排除时为空字符串。
    """
    data = context.get("data", {})
    gate_overrides = context.get("gate_overrides", {})

    l1_rules = load_pharma_rules()
    l2_rules = load_pharma_l2_rules() + load_research_l2_rules()

    excluded: dict[str, str] = {}

    for rule in l1_rules:
        code = rule.get("code", "")
        detection = rule.get("detection", {}) or {}
        exclude_when = detection.get("exclude_when", {}) or {}
        if not exclude_when:
            continue

        overrides = gate_overrides.get(code, {})
        if overrides.get("disable", False):
            continue

        if _match_exclude_condition(exclude_when, data):
            reason = _exclude_reason(rule, exclude_when)
            excluded[code] = reason

    for rule in l2_rules:
        code = rule.get("id", "")
        exclude_when = rule.get("exclude_when", {}) or {}
        if not exclude_when:
            continue

        if _match_exclude_condition(exclude_when, data):
            reason = _exclude_reason(rule, exclude_when)
            excluded[code] = reason

    if excluded:
        reasons = "; ".join(excluded.values())
        return excluded, f"排除规则触发: {reasons}"
    return {}, ""


def evaluate_rule(rule: dict[str, Any], data: dict[str, Any]) -> tuple[bool, str]:
    """评估单条规则的 exclude_when 条件。

    Args:
        rule: 规则字典。
        data: 待检测数据载荷。

    Returns:
        (is_excluded, reason)
    """
    detection = rule.get("detection", {}) or {}
    exclude_when = detection.get("exclude_when", {}) or {}
    if not exclude_when:
        return False, ""

    if _match_exclude_condition(exclude_when, data):
        return True, _exclude_reason(rule, exclude_when)
    return False, ""


def _match_exclude_condition(condition: dict[str, Any], data: dict[str, Any]) -> bool:
    """匹配单条排除条件。"""
    field = condition.get("field")
    operator = condition.get("operator", "eq")
    value = condition.get("value")

    if not field:
        return False

    actual = data.get(field)

    if operator == "eq":
        return actual == value
    if operator == "neq":
        return actual != value
    if operator == "in":
        if not isinstance(value, list):
            return False
        return actual in value
    if operator == "not_in":
        if not isinstance(value, list):
            return False
        return actual not in value
    if operator in ("gt", "gte", "lt", "lte"):
        try:
            a, v = float(actual), float(value)
        except (TypeError, ValueError):
            return False
        return {
            "gt": a > v,
            "gte": a >= v,
            "lt": a < v,
            "lte": a <= v,
        }.get(operator, False)

    return False


def _exclude_reason(rule: dict[str, Any], condition: dict[str, Any]) -> str:
    """生成排除原因描述。"""
    code = rule.get("code") or rule.get("id", "")
    name = rule.get("name", "")
    field = condition.get("field", "")
    value = condition.get("value", "")
    return f"[{code}] {name}: 条件 {field}={value} 满足排除"
