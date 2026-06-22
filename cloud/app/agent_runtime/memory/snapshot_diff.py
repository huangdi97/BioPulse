"""Snapshot diff utilities — compute, apply, serialize, and anchor step detection."""

import json


def _serialize(state_dict: dict) -> str:
    return json.dumps(state_dict, ensure_ascii=False, default=str)


def _deserialize(text: str | None) -> dict:
    if not text:
        return {}
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def _compute_diff(current: dict, previous: dict) -> dict:
    diff = {}
    for k in current:
        if k not in previous or previous[k] != current[k]:
            diff[k] = current[k]
    for k in previous:
        if k not in current:
            diff[k] = None
    diff["_is_diff"] = True
    return diff


def _apply_diff(base: dict, diff: dict) -> dict:
    result = dict(base)
    for k, v in diff.items():
        if k == "_is_diff":
            continue
        if v is None:
            result.pop(k, None)
        else:
            result[k] = v
    return result


def _is_anchor_step(step: int) -> bool:
    return step == 0 or step % 5 == 0
