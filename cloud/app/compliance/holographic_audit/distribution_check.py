"""Distribution-related anomaly detection patterns."""

from typing import Optional

from .decision import HolographicFinding
from .patterns import _detect_channel_stuffing, _detect_fake_distribution, _finding, _region_mismatch, _total, _trend


def check_channel_stuffing(
    expenses: list[dict],
    visits: list[dict],
    distributions: list[dict],
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


def check_management_neglect(
    expenses: list[dict],
    visits: list[dict],
    distributions: list[dict],
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


def check_channel_stuffing_batch(
    distributions: list[dict],
    distribution_area: list[dict] | None,
    expenses: list[dict],
    visits: list[dict],
    distributions_full: list[dict],
) -> Optional[HolographicFinding]:
    """Detect batch-level channel stuffing via authorized area data.

    Args:
        distributions: Distribution records for the check.
        distribution_area: Authorized area records.
        expenses: Expense records for context.
        visits: Visit records for context.
        distributions_full: Full distribution records for context.

    Returns:
        Finding when the pattern matches, otherwise None.
    """
    channel_result = _detect_channel_stuffing(distributions, distribution_area)
    if channel_result:
        return _finding(
            "channel_stuffing_batch",
            "distribution",
            channel_result["score"],
            channel_result["detail"],
            expenses,
            visits,
            distributions_full,
        )
    return None


def check_fake_distribution(
    sellin_data: list[dict],
    sellout_data: list[dict],
    expenses: list[dict],
    visits: list[dict],
    distributions: list[dict],
) -> Optional[HolographicFinding]:
    """Detect fake distribution through sell-in and sell-out comparison.

    Args:
        sellin_data: Sell-in records.
        sellout_data: Sell-out records.
        expenses: Expense records for context.
        visits: Visit records for context.
        distributions: Distribution records for context.

    Returns:
        Finding when the pattern matches, otherwise None.
    """
    fake_dist_result = _detect_fake_distribution(sellin_data, sellout_data)
    if fake_dist_result:
        return _finding(
            "fake_distribution",
            "distribution",
            fake_dist_result["score"],
            fake_dist_result["detail"],
            expenses,
            visits,
            distributions,
        )
    return None
