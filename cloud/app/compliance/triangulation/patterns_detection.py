"""Triangulation detection patterns — region analysis, channel stuffing, fake distribution & finding builder."""

from typing import Any

from .decision import TriangulationFinding
from .patterns_trend import _number, _period_values, _trend


def _region_mismatch(visits: list[dict[str, Any]], distributions: list[dict[str, Any]]) -> bool:
    """Check whether visit and distribution regions conflict.

    Args:
        visits: Visit records.
        distributions: Distribution records.

    Returns:
        True when regions are inconsistent, otherwise False.
    """
    visit_regions = _region_values(visits, ("region_id", "region", "visit_region", "authorized_region"))
    flow_regions = _region_values(distributions, ("actual_region", "flow_region", "distribution_region", "region_id", "region"))
    authorized = _region_values(distributions, ("authorized_region", "authorized_region_id"))
    if authorized and flow_regions and not flow_regions.issubset(authorized):
        return True
    return bool(visit_regions and flow_regions and visit_regions.isdisjoint(flow_regions))


def _region_values(records: list[dict[str, Any]], keys: tuple[str, ...]) -> set[str]:
    """Extract region values from records.

    Args:
        records: Records to inspect.
        keys: Candidate region keys.

    Returns:
        Set of non-empty region strings.
    """
    return {str(record[key]) for record in records for key in keys if record.get(key) not in (None, "")}


def _detect_channel_stuffing(
    distributions: list[dict[str, Any]],
    authorized_areas: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Detect channel stuffing — same batch/lot appears outside authorized area.

    Args:
        distributions: Distribution/flow records with batch and region info.
        authorized_areas: Authorized region/area records.

    Returns:
        Dict with score and detail when pattern matches, otherwise None.
    """
    if not distributions:
        return None
    batch_regions: dict[str, set[str]] = {}
    for dist in distributions:
        batch = dist.get("batch_no") or dist.get("lot_no") or dist.get("batch")
        region = dist.get("actual_region") or dist.get("flow_region") or dist.get("distribution_region") or dist.get("region_id")
        if batch and region:
            batch_regions.setdefault(str(batch), set()).add(str(region))
    if not batch_regions:
        return None
    authorized: set[str] = set()
    if authorized_areas:
        for area in authorized_areas:
            r = area.get("region_id") or area.get("region") or area.get("authorized_region")
            if r:
                authorized.add(str(r))
    mismatch_batches: list[str] = []
    for batch, regions in batch_regions.items():
        if authorized and not regions.issubset(authorized) or len(regions) > 1:
            mismatch_batches.append(batch)
    if not mismatch_batches:
        return None
    region_deviation = len(mismatch_batches) / max(len(batch_regions), 1)
    total_batch_qty = 0.0
    mismatch_qty = 0.0
    for dist in distributions:
        qty = _number(dist.get("quantity") or dist.get("qty") or dist.get("amount") or 0)
        batch = str(dist.get("batch_no") or dist.get("lot_no") or dist.get("batch", ""))
        if qty is not None:
            total_batch_qty += qty
            if batch in mismatch_batches:
                mismatch_qty += qty
    mismatch_ratio = mismatch_qty / max(total_batch_qty, 1.0)
    score = min(0.95, 0.5 + region_deviation * 0.3 + mismatch_ratio * 0.2)
    return {
        "score": round(score, 4),
        "detail": f"发现 {len(mismatch_batches)} 个批号出现在非授权区域或跨区域分布。",
        "signals": ["distribution_area_mismatch", "sellout_region_overflow"],
        "inputs": {
            "region_deviation": round(region_deviation, 4),
            "mismatch_ratio": round(mismatch_ratio, 4),
            "mismatch_batches": mismatch_batches,
        },
    }


def _detect_fake_distribution(
    sellin_data: list[dict[str, Any]],
    sellout_data: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Detect fake distribution — sellin grows while sellout is flat or declines.

    Args:
        sellin_data: Shipment/sell-in records.
        sellout_data: Actual sell-out/consumption records.

    Returns:
        Dict with score and detail when pattern matches, otherwise None.
    """
    if not sellin_data or not sellout_data:
        return None
    sellin_trend_val = _trend(sellin_data, "sellin")
    sellout_trend_val = _trend(sellout_data, "distribution")
    if not (sellin_trend_val == "up" and sellout_trend_val in {"flat", "down"}):
        return None
    sellin_prev, sellin_curr = _period_values(sellin_data, "sellin")
    sellout_prev, sellout_curr = _period_values(sellout_data, "distribution")
    gap_slope = 0.0
    inventory_days = 0.0
    if sellin_prev and sellin_curr and sellout_prev and sellout_curr:
        prev_gap = sellin_prev - sellout_prev
        curr_gap = sellin_curr - sellout_curr
        gap_slope = (curr_gap - prev_gap) / max(abs(prev_gap), 1.0)
        inventory_days = sellin_curr / max(sellout_curr, 1.0) * 30
    score = min(0.95, 0.5 + abs(gap_slope) * 0.3 + min(inventory_days / 90, 0.2))
    return {
        "score": round(score, 4),
        "detail": f"发货持续增长但纯销{'持平' if sellout_trend_val == 'flat' else '下降'}，渠道库存积压风险。",
        "signals": ["sellin_vs_sellout_gap", "channel_inventory_growth"],
        "inputs": {
            "gap_trend_slope": round(gap_slope, 4),
            "inventory_turnover_days": round(inventory_days, 2),
            "sellin_trend": sellin_trend_val,
            "sellout_trend": sellout_trend_val,
        },
    }


def _finding(
    pattern: str,
    category: str,
    score: float,
    detail: str,
    expenses: list[dict[str, Any]],
    visits: list[dict[str, Any]],
    distributions: list[dict[str, Any]],
) -> TriangulationFinding:
    """Build a triangulation finding.

    Args:
        pattern: Detection pattern id.
        category: Business category impacted by the finding.
        score: Confidence score.
        detail: Human-readable finding detail.
        expenses: Expense evidence records.
        visits: Visit evidence records.
        distributions: Distribution evidence records.

    Returns:
        TriangulationFinding instance.
    """
    confidence = "high" if score >= 0.8 else "medium" if score >= 0.5 else "low"
    decision = "trigger_red_light" if score >= 0.8 else "secondary_investigation" if score >= 0.5 else "mark_pending_review"
    return TriangulationFinding(
        pattern=pattern,
        category=category,
        score=round(score, 4),
        confidence=confidence,
        decision=decision,
        detail=detail,
        evidence={"expenses": expenses, "visits": visits, "distributions": distributions},
    )
