"""BD dashboard data aggregation — pipeline values, stage distribution, conversion rates, alerts."""

from __future__ import annotations

from typing import Any

from cloud.app.bd_pipeline.pipeline_service import BDPipelineService


class BDDashboardAggregator:
    """Aggregates BD pipeline data for the management dashboard."""

    def __init__(self, pipeline_service: BDPipelineService):
        self._pipeline = pipeline_service

    def overview(self) -> dict[str, Any]:
        """Return the BD dashboard overview."""
        summary = self._pipeline.summary()
        stages = summary.get("by_stage", [])
        stage_dist = {s["stage"]: {"count": s["count"], "amount": s["total_amount"]} for s in stages}
        total_deals = summary["total_deals"]
        weighted = summary["weighted_total"]
        closed_won = next((s for s in stages if s["stage"] == "closed_won"), None)
        conversion_rate = round((closed_won["count"] / max(total_deals, 1)) * 100, 2) if closed_won else 0.0
        return {
            "total_pipeline_value": round(sum(s["total_amount"] or 0.0 for s in stages), 2),
            "weighted_pipeline": weighted,
            "total_deals": total_deals,
            "stage_distribution": stage_dist,
            "conversion_rate": conversion_rate,
            "alerts": self._alerts(stages),
        }

    def _alerts(self, stages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Generate pipeline alerts for deals stuck or at risk."""
        alerts = []
        stuck = next((s for s in stages if s["stage"] == "prospecting"), None)
        if stuck and stuck["count"] > 10:
            alerts.append({"type": "warning", "message": f"超过 {stuck['count']} 个线索停留在 Prospecting 阶段", "stage": "prospecting"})
        negotiation = next((s for s in stages if s["stage"] == "negotiation"), None)
        if negotiation and (negotiation.get("avg_probability") or 0) < 0.5:
            alerts.append({"type": "risk", "message": "谈判阶段平均概率低于 50%", "stage": "negotiation"})
        return alerts

    def trend(self) -> dict[str, Any]:
        """Return pipeline trend data (placeholder for time-series)."""
        summary = self._pipeline.summary()
        return {
            "stages": summary.get("by_stage", []),
            "labels": ["本周", "本月", "本季度"],
            "values": [0, 0, summary.get("weighted_total", 0)],
        }
