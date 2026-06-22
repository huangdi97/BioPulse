"""Holographic audit trend analysis — token matching, period extraction & trend comparison."""

from typing import Any, Optional

UP_TOKENS = {"up", "increase", "increased", "rising", "rise", "high", "higher", "↑", "+", "增长", "上升", "增加", "虚高"}
DOWN_TOKENS = {"down", "decrease", "decreased", "falling", "drop", "low", "lower", "↓", "-", "下降", "减少", "下滑"}
FLAT_TOKENS = {"flat", "stable", "same", "unchanged", "→", "0", "持平", "不变", "稳定"}
VOLATILE_TOKENS = {"volatile", "mismatch", "cross_region", "updown", "↑↓", "↓↑", "窜货", "背离", "不符"}


def _trend(records: list[dict[str, Any]], dimension: str) -> str:
    """Infer directional trend for a business dimension.

    Args:
        records: Records to inspect.
        dimension: Dimension name such as expense, visit, or distribution.

    Returns:
        One of up, down, flat, volatile, or unknown.
    """
    explicit = _explicit_trend(records, dimension)
    if explicit != "unknown":
        return explicit
    previous, current = _period_values(records, dimension)
    if previous is None or current is None:
        return "unknown"
    return _compare_trend(previous, current)


def _explicit_trend(records: list[dict[str, Any]], dimension: str) -> str:
    """Read explicit trend labels from records.

    Args:
        records: Records to inspect.
        dimension: Dimension name to search.

    Returns:
        Parsed trend or unknown.
    """
    aliases = {
        "expense": ("expense_trend", "amount_trend", "trend", "direction"),
        "visit": ("visit_trend", "visit_count_trend", "trend", "direction"),
        "distribution": ("distribution_trend", "flow_trend", "sellout_trend", "trend", "direction"),
        "sellin": ("sellin_trend", "shipment_trend", "trend", "direction"),
    }
    for record in records:
        for key in aliases.get(dimension, ("trend",)):
            parsed = _parse_trend(record.get(key))
            if parsed != "unknown":
                return parsed
    return "unknown"


def _parse_trend(value: Any) -> str:
    """Parse a trend value into a normalized direction.

    Args:
        value: Trend value to parse.

    Returns:
        Normalized trend string.
    """
    text = str(value or "").strip().lower()
    if text in VOLATILE_TOKENS:
        return "volatile"
    if text in UP_TOKENS:
        return "up"
    if text in DOWN_TOKENS:
        return "down"
    if text in FLAT_TOKENS:
        return "flat"
    return "unknown"


def _period_values(records: list[dict[str, Any]], dimension: str) -> tuple[Optional[float], Optional[float]]:
    """Extract previous and current values from records.

    Args:
        records: Records to inspect.
        dimension: Business dimension name.

    Returns:
        Previous and current numeric values when available.
    """
    previous_keys, current_keys = _dimension_keys(dimension)
    previous = _first_number(records, previous_keys)
    current = _first_number(records, current_keys)
    if previous is not None and current is not None:
        return previous, current
    if len(records) >= 2:
        midpoint = max(len(records) // 2, 1)
        return _sum_records(records[:midpoint], current_keys), _sum_records(records[midpoint:], current_keys)
    return None, None


def _dimension_keys(dimension: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return previous and current metric keys for a dimension.

    Args:
        dimension: Business dimension name.

    Returns:
        Tuple of previous-key tuple and current-key tuple.
    """
    keys = {
        "expense": (("previous_expense", "previous_amount", "last_amount"), ("current_expense", "amount", "expense_amount", "total_amount")),
        "visit": (("previous_visit_count", "previous_visits", "last_visit_count"), ("current_visit_count", "visit_count", "count", "visits")),
        "distribution": (
            ("previous_distribution", "previous_flow", "previous_sellout", "last_distribution"),
            ("current_distribution", "distribution", "flow", "sellout", "sales_qty", "quantity"),
        ),
        "sellin": (
            ("previous_sellin", "previous_shipment", "last_shipment"),
            ("current_sellin", "sellin", "shipment", "sellin_qty"),
        ),
    }
    return keys.get(dimension, (("previous",), ("current",)))


def _first_number(records: list[dict[str, Any]], keys: tuple[str, ...]) -> Optional[float]:
    """Return the first numeric value found for keys.

    Args:
        records: Records to inspect.
        keys: Candidate metric keys.

    Returns:
        Numeric value or None.
    """
    for record in records:
        for key in keys:
            number = _number(record.get(key))
            if number is not None:
                return number
    return None


def _sum_records(records: list[dict[str, Any]], keys: tuple[str, ...]) -> Optional[float]:
    """Sum numeric values for candidate keys across records.

    Args:
        records: Records to aggregate.
        keys: Candidate metric keys.

    Returns:
        Sum of numeric values or None.
    """
    values = [_number(record.get(key)) for record in records for key in keys if _number(record.get(key)) is not None]
    return sum(values) if values else None


def _number(value: Any) -> Optional[float]:
    """Convert a value to a float when possible.

    Args:
        value: Value to convert.

    Returns:
        Float value or None.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compare_trend(previous: float, current: float) -> str:
    """Compare previous and current values into a trend.

    Args:
        previous: Previous numeric value.
        current: Current numeric value.

    Returns:
        up, down, or flat.
    """
    base = abs(previous) or 1.0
    ratio = (current - previous) / base
    if ratio >= 0.15:
        return "up"
    if ratio <= -0.15:
        return "down"
    return "flat"


def _total(records: list[dict[str, Any]], keys: tuple[str, ...]) -> float:
    """Sum numeric fields across records.

    Args:
        records: Records to aggregate.
        keys: Candidate field names.

    Returns:
        Numeric total.
    """
    return sum(_number(record.get(key)) or 0.0 for record in records for key in keys)
