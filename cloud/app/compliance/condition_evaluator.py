"""L2 rule condition matchers and numeric helpers."""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _float(value: Any) -> Optional[float]:
    try:
        return float(value) if value is not None else 0.0
    except (TypeError, ValueError):
        return None


def _count(row: Any) -> int:
    return int(row["c"] if hasattr(row, "keys") and "c" in row.keys() else row[0])


def _compare(value: Any, operator: str, threshold: Any) -> bool:
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


def _match_value_threshold(
    rule: dict[str, Any], data: dict[str, Any], condition: dict[str, Any], threshold: Any
) -> Optional[dict[str, Any]]:
    field = condition.get("field")
    value, expected = _float(data.get(field)), _float(threshold)
    if value is not None and expected is not None and _compare(value, condition.get("operator", "gt"), expected):
        return _l2_violation(rule, f"字段[{field}]值[{value}]超出阈值[{expected}]")
    return None


def _match_flag_check(
    rule: dict[str, Any], data: dict[str, Any], condition: dict[str, Any]
) -> Optional[dict[str, Any]]:
    field = condition.get("field")
    expected = condition.get("expected")
    if data.get(field) != expected:
        return _l2_violation(rule, f"字段[{field}]期望值[{expected}]，实际值[{data.get(field)}]")
    return None


def _match_frequency_count(
    db: Any, rule: dict[str, Any], data: dict[str, Any], condition: dict[str, Any], threshold: Any
) -> Optional[dict[str, Any]]:
    field = condition.get("field")
    entity_id = data.get(field)
    if entity_id is None:
        return None
    window_days = condition.get("window_days", 7)
    since = (datetime.now() - timedelta(days=window_days)).isoformat()
    count = _count(
        db.execute(
            f"SELECT COUNT(*) AS c FROM visits WHERE {field} = ? AND created_at >= ?",
            (entity_id, since),
        ).fetchone()
    )
    if count >= int(threshold):
        return _l2_violation(rule, f"实体[{entity_id}]在{window_days}天内拜访{count}次，阈值[{threshold}]")
    return None


def _match_concentration_check(
    db: Any, rule: dict[str, Any], data: dict[str, Any], condition: dict[str, Any]
) -> Optional[dict[str, Any]]:
    field = condition.get("field")
    value = data.get(field)
    if value is None:
        return None
    window_days = condition.get("window_days", 30)
    since = (datetime.now() - timedelta(days=window_days)).isoformat()
    total = _count(db.execute("SELECT COUNT(*) AS c FROM visits WHERE created_at >= ?", (since,)).fetchone())
    if total <= 0:
        return None
    matched = _count(
        db.execute(
            f"SELECT COUNT(*) AS c FROM visits WHERE {field} = ? AND created_at >= ?", (value, since)
        ).fetchone()
    )
    ratio = matched / total
    threshold = condition.get("ratio_threshold", 0.8)
    if ratio >= threshold:
        return _l2_violation(rule, f"值[{value}]占比{ratio:.1%}，阈值[{threshold:.0%}]")
    return None


def _match_citation_check(
    rule: dict[str, Any], data: dict[str, Any], condition: dict[str, Any]
) -> Optional[dict[str, Any]]:
    field = condition.get("field")
    expected = condition.get("expected")
    if data.get(field) != expected:
        return _l2_violation(rule, f"引用未验证，字段[{field}]值[{data.get(field)}]")
    return None


def _match_expiry_check(
    rule: dict[str, Any], data: dict[str, Any], condition: dict[str, Any]
) -> Optional[dict[str, Any]]:
    field = condition.get("field")
    expiry = data.get(field)
    if not expiry:
        return None
    try:
        expiry_date = datetime.fromisoformat(expiry) if isinstance(expiry, str) else expiry
        remaining = (expiry_date - datetime.now()).days if isinstance(expiry_date, datetime) else None
        lead_days = condition.get("lead_days", 90)
        if remaining is not None and remaining <= lead_days:
            return _l2_violation(rule, f"资质{remaining}天后到期，预警期{lead_days}天")
    except (TypeError, ValueError):
        logger.warning("Failed to parse expiry date for L2 compliance rule", exc_info=True)
    return None


def _match_discount_check(
    rule: dict[str, Any], data: dict[str, Any], condition: dict[str, Any], threshold: Any
) -> Optional[dict[str, Any]]:
    field = condition.get("field")
    value, expected = _float(data.get(field)), _float(threshold)
    value = 1.0 if value is None else value
    operator = condition.get("operator", "lt")
    if expected is not None and operator == "lt" and value < expected:
        return _l2_violation(rule, f"折扣率{value:.0%}低于阈值{expected:.0%}")
    if expected is not None and operator == "gt" and value > expected:
        return _l2_violation(rule, f"折扣率{value:.0%}超过阈值{expected:.0%}")
    return None


def _l2_violation(rule: dict[str, Any], detail: str) -> dict[str, Any]:
    return {
        "rule_id": rule.get("id"),
        "rule_name": rule.get("name"),
        "severity": rule.get("severity"),
        "check_type": rule.get("check_type"),
        "detail": f"L2规则'{rule.get('id')}'触发: {rule.get('name')}. {detail}",
    }
