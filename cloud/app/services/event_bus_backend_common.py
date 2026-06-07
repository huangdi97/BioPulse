"""Shared event bus backend helpers."""

import json

ALL_ENDS = ["cloud", "sales-coach", "sales-assistant", "assistant", "opportunity"]


def parse_targets(raw):
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        return parsed if parsed else ALL_ENDS.copy()
    except (json.JSONDecodeError, TypeError):
        return ALL_ENDS.copy()
