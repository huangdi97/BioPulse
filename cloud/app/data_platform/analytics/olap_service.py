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
        """初始化 OLAP 服务，将输入行转换为列表。

        参数:
            rows: 可选，可迭代的字典行数据。

        返回:
            None
        """
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
        """执行多维聚合查询，按维度分组并计算指标。

        参数:
            dimensions: 维度字段列表，默认为 ["activity_date"]。
            metrics: 指标及其聚合方式字典，默认为 DEFAULT_METRICS。
            filters: 筛选条件字典。
            date_from: 起始日期筛选。
            date_to: 结束日期筛选。
            limit: 返回结果数量上限，默认为 100。

        返回:
            聚合结果字典列表。
        """
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
        """根据维度、指标和筛选条件构建 SQL 查询语句。

        参数:
            fact_table: 事实表名，默认为 "fact_business_activity_daily"。
            dimensions: 维度字段列表，默认为 [date_column, "team_id"]。
            metrics: 指标及其聚合方式字典，默认为 DEFAULT_METRICS。
            filters: 筛选条件字典。
            date_column: 日期列名，默认为 "activity_date"。

        返回:
            生成的 SQL 查询字符串。
        """
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
        """根据筛选条件和日期范围过滤数据行。

        参数:
            filters: 字段精确匹配筛选条件。
            date_from: 起始日期（含）。
            date_to: 结束日期（含）。

        返回:
            过滤后的行字典列表。
        """
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
        """对指定指标在行数据上执行聚合计算。

        参数:
            rows: 数据行列表。
            metric: 指标字段名。
            aggregation: 聚合方式（count/avg/min/max/sum）。

        返回:
            聚合计算结果（float 或 int）。
        """
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
