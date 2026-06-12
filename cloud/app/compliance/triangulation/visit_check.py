"""Visit-related anomaly detection patterns."""

from typing import Optional

from .decision import TriangulationFinding
from .patterns import _finding, _total, _trend


def check_visit_fraud(
    expenses: list[dict],
    visits: list[dict],
    distributions: list[dict],
) -> Optional[TriangulationFinding]:
    """Detect fabricated visits where visit volume rises without flow change.

    Args:
        expenses: Normalized expense records.
        visits: Normalized visit records.
        distributions: Normalized distribution records.

    Returns:
        Finding when the pattern matches, otherwise None.
    """
    visit, flow = _trend(visits, "visit"), _trend(distributions, "distribution")
    if visit == "up" and flow in {"flat", "down"}:
        score = 0.82 if _total(visits, ("visit_count", "count", "visits")) >= 20 else 0.68
        return _finding("visit_fraud", "visit", score, "拜访量上升但流向未同步增长。", expenses, visits, distributions)
    return None


def check_fake_activity(
    expenses: list[dict],
    visits: list[dict],
    distributions: list[dict],
) -> Optional[TriangulationFinding]:
    """Detect fake activity where expenses and visits rise while sell-out falls.

    Args:
        expenses: Normalized expense records.
        visits: Normalized visit records.
        distributions: Normalized distribution records.

    Returns:
        Finding when the pattern matches, otherwise None.
    """
    expense, visit, flow = _trend(expenses, "expense"), _trend(visits, "visit"), _trend(distributions, "distribution")
    if expense == "up" and visit == "up" and flow == "down":
        return _finding("fake_activity", "activity", 0.94, "费用与拜访量双增但纯销或流向下降。", expenses, visits, distributions)
    return None
