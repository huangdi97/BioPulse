"""Evidence scoring and level rule functions."""

from typing import Any

from shared.base import AppException, ErrorCode


def evidence_score(evidence: dict[str, Any]) -> float:
    explicit = evidence.get("confidence_score", evidence.get("score"))
    if explicit is not None:
        try:
            return max(0.0, min(float(explicit), 1.0))
        except (TypeError, ValueError):
            return 0.0
    severity = str(evidence.get("severity", evidence.get("confidence", ""))).lower()
    return {"high": 0.9, "critical": 0.95, "medium": 0.65, "warning": 0.55, "low": 0.35}.get(severity, 0.0)


def level_from_score(score: float) -> str:
    if score >= 0.9:
        return "L3"
    if score >= 0.78:
        return "L2"
    return "L1"


def level_rank(level: str) -> int:
    return {"L1": 1, "L2": 2, "L3": 3}.get(level, 0)


def should_revoke(evidence: dict[str, Any]) -> bool:
    action = str(evidence.get("action", "")).lower()
    return bool(evidence.get("exonerating") or evidence.get("resolved") or action in {"revoke", "withdraw", "clear"})


def normalize_level(level: str) -> str:
    normalized = str(level or "").upper()
    if normalized not in {"L1", "L2", "L3"}:
        raise AppException(ErrorCode.VALIDATION_ERROR, f"Unsupported red-light level: {level}")
    return normalized
