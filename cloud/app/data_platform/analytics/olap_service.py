"""OLAP query service for multidimensional aggregation."""

from collections import defaultdict
from typing import Any, Iterable


class OLAPService:
    """Run multidimensional aggregations over in-memory rows or SQL metadata."""

    DEFAULT_METRICS = {
        "visit_count": "sum",
        "engagement_score": "avg",
        "opportunity_amount": "sum",
        "compliance_issue_count": "sum",
    }

    def __init__(self, rows: Iterable[dict[str, Any]] | None = None) -> None:
        self.rows = list(rows or [])

    def query(
        self,
        dimensions: list[str] | None = None,
        metrics: dict[str, str] | None = None,
        filters: dict[str, Any] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        dimensions = dimensions or ["activity_date"]
        metrics = metrics or self.DEFAULT_METRICS
        filtered_rows = self._filter_rows(filters or {}, date_from, date_to)
        buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)

        for row in filtered_rows:
            key = tuple(row.get(dimension) for dimension in dimensions)
            buckets[key].append(row)

        results = []
        for key, bucket_rows in buckets.items():
            result = {dimension: value for dimension, value in zip(dimensions, key)}
            for metric, aggregation in metrics.items():
                result[metric] = self._aggregate(bucket_rows, metric, aggregation)
            results.append(result)

        return results[:limit]

    def build_sql(
        self,
        fact_table: str = "fact_business_activity_daily",
        dimensions: list[str] | None = None,
        metrics: dict[str, str] | None = None,
        filters: dict[str, Any] | None = None,
        date_column: str = "activity_date",
    ) -> str:
        dimensions = dimensions or [date_column, "team_id"]
        metrics = metrics or self.DEFAULT_METRICS
        select_parts = [*dimensions]
        for metric, aggregation in metrics.items():
            select_parts.append(f"{aggregation.upper()}({metric}) AS {metric}")
        where_parts = [f"{column} = :{column}" for column in (filters or {})]
        where_sql = f"\nWHERE {' AND '.join(where_parts)}" if where_parts else ""
        group_sql = ", ".join(dimensions)
        return "SELECT\n  " + ",\n  ".join(select_parts) + f"\nFROM {fact_table}" + where_sql + f"\nGROUP BY {group_sql}"

    def _filter_rows(
        self,
        filters: dict[str, Any],
        date_from: str | None,
        date_to: str | None,
    ) -> list[dict[str, Any]]:
        rows = []
        for row in self.rows:
            if any(row.get(key) != value for key, value in filters.items()):
                continue
            row_date = row.get("activity_date") or row.get("date")
            if date_from and row_date and row_date < date_from:
                continue
            if date_to and row_date and row_date > date_to:
                continue
            rows.append(row)
        return rows

    @staticmethod
    def _aggregate(rows: list[dict[str, Any]], metric: str, aggregation: str) -> float | int:
        values = [row.get(metric, 0) or 0 for row in rows]
        if aggregation == "count":
            return len(values)
        if not values:
            return 0
        if aggregation == "avg":
            return round(sum(values) / len(values), 4)
        if aggregation == "min":
            return min(values)
        if aggregation == "max":
            return max(values)
        return sum(values)
