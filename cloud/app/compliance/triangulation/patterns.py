"""Triangulation detection patterns — entry point re-exporting all public symbols."""

from typing import Any

from shared.base import AppException, ErrorCode


def _records(value: dict[str, Any] | list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Normalize an input payload into a list of dictionaries.

    Args:
        value: Optional dictionary or list of dictionaries.

    Returns:
        Normalized list of dictionaries.
    """
    if value is None:
        return []
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    raise AppException(ErrorCode.VALIDATION_ERROR, "Triangulation data must be a dict, list, or None")


def _row_to_dict(row: Any) -> dict[str, Any]:
    """Convert a sqlite row or tuple to a dictionary.

    Args:
        row: SQLite row object.

    Returns:
        Row dictionary.
    """
    if hasattr(row, "keys"):
        return {key: row[key] for key in row.keys()}
    return {}


def _correlation_keys(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract correlation keys from records.

    Args:
        records: Records to scan.

    Returns:
        Dictionary of correlation keys.
    """
    keys = ("visit_id", "rep_id", "hcp_id", "product_id", "region_id", "distributor_id")
    result: dict[str, Any] = {}
    for record in records:
        for key in keys:
            result.setdefault(key, record.get(key))
    return {key: value for key, value in result.items() if value not in (None, "")}
