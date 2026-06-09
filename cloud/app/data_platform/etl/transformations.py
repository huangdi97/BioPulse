"""dbt-style SQL transformations for the data platform."""

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class SQLModel:
    name: str
    sql: str
    materialized: str = "view"
    depends_on: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""

    def compile(self) -> str:
        if self.materialized == "table":
            return f"CREATE TABLE IF NOT EXISTS {self.name} AS\n{self.sql.strip()};"
        return f"CREATE VIEW IF NOT EXISTS {self.name} AS\n{self.sql.strip()};"


def ref(model_name: str) -> str:
    """Return a dbt-like model reference token."""

    return model_name


def source(source_name: str, table_name: str) -> str:
    """Return a dbt-like source reference."""

    return f"{source_name}.{table_name}"


def build_staging_model(name: str, raw_table: str, columns: Iterable[str], tenant_column: str = "tenant_id") -> SQLModel:
    selected_columns = ",\n    ".join(dict.fromkeys([tenant_column, *columns]))
    return SQLModel(
        name=name,
        materialized="view",
        depends_on=(raw_table,),
        description=f"Staging cleanup for {raw_table}.",
        sql=f"""
SELECT
    {selected_columns}
FROM {raw_table}
WHERE {tenant_column} IS NOT NULL
""",
    )


def build_incremental_fact_model(
    name: str,
    staging_table: str,
    dimensions: Iterable[str],
    metrics: Iterable[str],
    date_column: str = "date",
) -> SQLModel:
    dimension_sql = ",\n    ".join(dimensions)
    metric_sql = ",\n    ".join(f"SUM({metric}) AS {metric}" for metric in metrics)
    group_by = ", ".join([date_column, *dimensions])
    select_parts = ",\n    ".join(part for part in [date_column, dimension_sql, metric_sql] if part)
    return SQLModel(
        name=name,
        materialized="table",
        depends_on=(staging_table,),
        description=f"Incremental fact aggregation from {staging_table}.",
        sql=f"""
SELECT
    {select_parts}
FROM {staging_table}
GROUP BY {group_by}
""",
    )


def build_dimension_model(
    name: str,
    staging_table: str,
    key_column: str,
    attributes: Iterable[str],
) -> SQLModel:
    selected_columns = ",\n    ".join(dict.fromkeys([key_column, *attributes]))
    return SQLModel(
        name=name,
        materialized="table",
        depends_on=(staging_table,),
        description=f"Deduplicated dimension {name}.",
        sql=f"""
SELECT DISTINCT
    {selected_columns}
FROM {staging_table}
WHERE {key_column} IS NOT NULL
""",
    )


def compile_models(models: Iterable[SQLModel]) -> list[str]:
    return [model.compile() for model in models]


DEFAULT_TRANSFORMATIONS = [
    build_staging_model(
        name="stg_business_activity",
        raw_table="raw_business_activity",
        columns=[
            "activity_id",
            "activity_date",
            "team_id",
            "customer_id",
            "product_id",
            "activity_type",
            "visit_count",
            "engagement_score",
            "opportunity_amount",
            "compliance_issue_count",
        ],
    ),
    build_incremental_fact_model(
        name="fact_business_activity_daily",
        staging_table=ref("stg_business_activity"),
        dimensions=["tenant_id", "team_id", "customer_id", "product_id", "activity_type"],
        metrics=["visit_count", "engagement_score", "opportunity_amount", "compliance_issue_count"],
        date_column="activity_date",
    ),
]
