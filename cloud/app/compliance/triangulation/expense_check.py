"""Expense-related anomaly detection patterns."""

from typing import Optional

from .decision import TriangulationFinding
from .patterns import _finding, _trend


def check_expense_waste(
    expenses: list[dict],
    visits: list[dict],
    distributions: list[dict],
) -> Optional[TriangulationFinding]:
    """Detect expense waste where expense rises while visits and flow fall.

    Args:
        expenses: Normalized expense records.
        visits: Normalized visit records.
        distributions: Normalized distribution records.

    Returns:
        Finding when the pattern matches, otherwise None.
    """
    expense, visit, flow = _trend(expenses, "expense"), _trend(visits, "visit"), _trend(distributions, "distribution")
    if expense == "up" and visit == "down" and flow == "down":
        return _finding("expense_waste", "expense", 0.86, "代表费用上升但拜访与流向同步下降。", expenses, visits, distributions)
    if expense == "up" and visit in {"down", "flat"} and flow in {"down", "flat"}:
        return _finding("expense_waste", "expense", 0.72, "代表费用上升但业务活动或流向未同步改善。", expenses, visits, distributions)
    return None
