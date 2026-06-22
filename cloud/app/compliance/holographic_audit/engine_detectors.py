"""Holographic audit anomaly detection pattern functions."""

from __future__ import annotations

from typing import Any, Optional

from .decision import HolographicFinding
from .patterns import _records
from .patterns_detection import _detect_channel_stuffing, _detect_fake_distribution, _finding, _region_mismatch
from .patterns_trend import _total, _trend


def _expense_waste(expenses: list[dict[str, Any]], visits: list[dict[str, Any]], distributions: list[dict[str, Any]]) -> Optional[HolographicFinding]:
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


def _visit_fraud(expenses: list[dict[str, Any]], visits: list[dict[str, Any]], distributions: list[dict[str, Any]]) -> Optional[HolographicFinding]:
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


def _channel_stuffing(
    expenses: list[dict[str, Any]], visits: list[dict[str, Any]], distributions: list[dict[str, Any]]
) -> Optional[HolographicFinding]:
    """Detect cross-region or inconsistent distribution flow.

    Args:
        expenses: Normalized expense records.
        visits: Normalized visit records.
        distributions: Normalized distribution records.

    Returns:
        Finding when the pattern matches, otherwise None.
    """
    if _region_mismatch(visits, distributions) or _trend(distributions, "distribution") == "volatile":
        return _finding("channel_stuffing", "distribution", 0.9, "流向与授权区域、拜访区域或正常波动不一致。", expenses, visits, distributions)
    return None


def _management_neglect(
    expenses: list[dict[str, Any]], visits: list[dict[str, Any]], distributions: list[dict[str, Any]]
) -> Optional[HolographicFinding]:
    """Detect management neglect over repeated unresolved red lights.

    Args:
        expenses: Normalized expense records.
        visits: Normalized visit records.
        distributions: Normalized distribution records.

    Returns:
        Finding when the pattern matches, otherwise None.
    """
    records = expenses + visits + distributions
    red_lights = _total(records, ("red_light_count", "red_lights", "unresolved_red_lights"))
    unresolved = _total(records, ("unresolved_red_lights", "unhandled_red_lights"))
    actions = _total(records, ("manager_action_count", "manager_followup_count", "handled_red_lights"))
    if red_lights >= 2 and unresolved >= 1 and actions == 0:
        return _finding("management_neglect", "management", 0.88, "多次红灯未处理且缺少管理动作。", expenses, visits, distributions)
    return None


def _fake_activity(expenses: list[dict[str, Any]], visits: list[dict[str, Any]], distributions: list[dict[str, Any]]) -> Optional[HolographicFinding]:
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


def _evaluate_patterns(
    expenses: list[dict[str, Any]],
    visits: list[dict[str, Any]],
    distributions: list[dict[str, Any]],
    distribution_area: dict[str, Any] | list[dict[str, Any]] | None = None,
    sellin_data: dict[str, Any] | list[dict[str, Any]] | None = None,
    sellout_data: dict[str, Any] | list[dict[str, Any]] | None = None,
) -> list[HolographicFinding]:
    """Evaluate all seven detection patterns.

    Args:
        expenses: Normalized expense records.
        visits: Normalized visit records.
        distributions: Normalized distribution records.
        distribution_area: Authorized area records for channel stuffing detection.
        sellin_data: Sell-in records for fake distribution detection.
        sellout_data: Sell-out records for fake distribution detection.

    Returns:
        List of findings produced by matched patterns.
    """
    findings = []
    for finder in (
        _expense_waste,
        _visit_fraud,
        _channel_stuffing,
        _management_neglect,
        _fake_activity,
    ):
        finding = finder(expenses, visits, distributions)
        if finding:
            findings.append(finding)

    channel_result = _detect_channel_stuffing(distributions, _records(distribution_area))
    if channel_result:
        findings.append(
            _finding(
                "channel_stuffing_batch",
                "distribution",
                channel_result["score"],
                channel_result["detail"],
                expenses,
                visits,
                distributions,
            )
        )

    sellin_records = _records(sellin_data)
    sellout_records = _records(sellout_data)
    fake_dist_result = _detect_fake_distribution(
        sellin_records or distributions,
        sellout_records or distributions,
    )
    if fake_dist_result:
        findings.append(
            _finding(
                "fake_distribution",
                "distribution",
                fake_dist_result["score"],
                fake_dist_result["detail"],
                expenses,
                visits,
                distributions,
            )
        )

    return findings
