import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


def row_to_dict(row, *json_cols: str) -> dict:
    d = dict(row)
    for col in json_cols:
        if col in d and isinstance(d[col], str) and d[col]:
            try:
                d[col] = json.loads(d[col])
            except (json.JSONDecodeError, TypeError):
                logger.warning("Failed to parse JSON field '%s'", col, exc_info=True)
    return d
