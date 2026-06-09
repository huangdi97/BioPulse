"""Embedded BI report data interface for admin views."""

from typing import Any, Iterable

from cloud.app.data_platform.analytics.olap_service import OLAPService


class BIViewService:
    """Prepare BI report datasets aggregated by date, team, and metric."""

    def __init__(self, rows: Iterable[dict[str, Any]] | None = None) -> None:
        self.olap = OLAPService(rows=rows)

    def report_data(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        team_id: str | None = None,
        metrics: list[str] | None = None,
        group_by: list[str] | None = None,
    ) -> dict[str, Any]:
        group_by = group_by or ["activity_date", "team_id"]
        metric_names = metrics or ["visit_count", "engagement_score", "opportunity_amount"]
        filters = {"team_id": team_id} if team_id else {}
        metric_map = {metric: ("avg" if metric.endswith("_score") or metric == "engagement_score" else "sum") for metric in metric_names}
        rows = self.olap.query(
            dimensions=group_by,
            metrics=metric_map,
            filters=filters,
            date_from=date_from,
            date_to=date_to,
            limit=1000,
        )
        totals = self._totals(rows, metric_map)
        return {
            "filters": {
                "date_from": date_from,
                "date_to": date_to,
                "team_id": team_id,
                "group_by": group_by,
                "metrics": metric_names,
            },
            "rows": rows,
            "totals": totals,
            "chart": self._chart(rows, group_by, metric_names),
        }

    @staticmethod
    def _totals(rows: list[dict[str, Any]], metric_map: dict[str, str]) -> dict[str, float | int]:
        totals: dict[str, float | int] = {}
        for metric, aggregation in metric_map.items():
            values = [row.get(metric, 0) or 0 for row in rows]
            if aggregation == "avg":
                totals[metric] = round(sum(values) / len(values), 4) if values else 0
            else:
                totals[metric] = sum(values)
        return totals

    @staticmethod
    def _chart(rows: list[dict[str, Any]], group_by: list[str], metrics: list[str]) -> dict[str, Any]:
        label_columns = group_by[:2]
        return {
            "labels": [" / ".join(str(row.get(column, "")) for column in label_columns) for row in rows],
            "series": [{"name": metric, "data": [row.get(metric, 0) or 0 for row in rows]} for metric in metrics],
        }
