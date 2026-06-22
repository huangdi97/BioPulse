"""Confidence score to suspicion level / decision mapping."""

from __future__ import annotations


def _level(score: float) -> str:
    """Convert confidence score to suspicion level.

    Args:
        score: Confidence score between 0 and 1.

    Returns:
        Suspicion level string.
    """
    if score >= 0.8:
        return "high"
    if score >= 0.5:
        return "medium"
    if score > 0:
        return "low"
    return "none"


def _decision(score: float) -> str:
    """Convert confidence score to a decision.

    Args:
        score: Confidence score between 0 and 1.

    Returns:
        Decision string.
    """
    if score >= 0.8:
        return "trigger_red_light"
    if score >= 0.5:
        return "secondary_investigation"
    if score > 0:
        return "mark_pending_review"
    return "pass"
