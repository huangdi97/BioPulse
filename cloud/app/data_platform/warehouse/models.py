"""数据仓库星型模型定义。"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class WarehouseColumn:
    name: str
    data_type: str
    nullable: bool = True
    description: str = ""

    def ddl(self) -> str:
        null_expr = "" if self.nullable else " NOT NULL"
        return f"{self.name} {self.data_type}{null_expr}"


@dataclass(frozen=True)
class DimensionTable:
    name: str
    key: str
    columns: tuple[WarehouseColumn, ...]
    description: str = ""

    def ddl(self) -> str:
        column_sql = ",\n  ".join(column.ddl() for column in self.columns)
        return f"CREATE TABLE IF NOT EXISTS {self.name} (\n  {column_sql},\n  PRIMARY KEY ({self.key})\n);"


@dataclass(frozen=True)
class FactTable:
    name: str
    grain: str
    measures: tuple[WarehouseColumn, ...]
    foreign_keys: dict[str, str]
    degenerate_dimensions: tuple[WarehouseColumn, ...] = field(default_factory=tuple)
    description: str = ""

    def ddl(self) -> str:
        columns = [
            WarehouseColumn("fact_id", "TEXT", nullable=False),
            WarehouseColumn("tenant_id", "TEXT", nullable=False),
            *self.degenerate_dimensions,
            *[WarehouseColumn(name, "TEXT", nullable=False) for name in self.foreign_keys],
            *self.measures,
        ]
        column_sql = ",\n  ".join(column.ddl() for column in columns)
        fk_sql = ",\n  ".join(f"FOREIGN KEY ({column}) REFERENCES {table}({column})" for column, table in self.foreign_keys.items())
        constraints = f",\n  {fk_sql}" if fk_sql else ""
        return f"CREATE TABLE IF NOT EXISTS {self.name} (\n  {column_sql},\n  PRIMARY KEY (fact_id){constraints}\n);"


class StarSchema:
    """医药商业分析星型模型。"""

    def __init__(self) -> None:
        self.dimensions = {
            "dim_date": DimensionTable(
                name="dim_date",
                key="date_id",
                description="日期维度，支持按日、周、月、季度聚合。",
                columns=(
                    WarehouseColumn("date_id", "TEXT", nullable=False),
                    WarehouseColumn("date", "DATE", nullable=False),
                    WarehouseColumn("week", "INTEGER", nullable=False),
                    WarehouseColumn("month", "INTEGER", nullable=False),
                    WarehouseColumn("quarter", "INTEGER", nullable=False),
                    WarehouseColumn("year", "INTEGER", nullable=False),
                ),
            ),
            "dim_team": DimensionTable(
                name="dim_team",
                key="team_id",
                description="销售与医学团队维度。",
                columns=(
                    WarehouseColumn("team_id", "TEXT", nullable=False),
                    WarehouseColumn("tenant_id", "TEXT", nullable=False),
                    WarehouseColumn("team_name", "TEXT", nullable=False),
                    WarehouseColumn("region", "TEXT"),
                    WarehouseColumn("manager_name", "TEXT"),
                ),
            ),
            "dim_customer": DimensionTable(
                name="dim_customer",
                key="customer_id",
                description="客户/HCP/机构维度。",
                columns=(
                    WarehouseColumn("customer_id", "TEXT", nullable=False),
                    WarehouseColumn("tenant_id", "TEXT", nullable=False),
                    WarehouseColumn("customer_name", "TEXT", nullable=False),
                    WarehouseColumn("segment", "TEXT"),
                    WarehouseColumn("city", "TEXT"),
                    WarehouseColumn("institution_level", "TEXT"),
                ),
            ),
            "dim_product": DimensionTable(
                name="dim_product",
                key="product_id",
                description="产品维度。",
                columns=(
                    WarehouseColumn("product_id", "TEXT", nullable=False),
                    WarehouseColumn("tenant_id", "TEXT", nullable=False),
                    WarehouseColumn("product_name", "TEXT", nullable=False),
                    WarehouseColumn("therapeutic_area", "TEXT"),
                    WarehouseColumn("lifecycle_stage", "TEXT"),
                ),
            ),
        }
        self.facts = {
            "fact_business_activity": FactTable(
                name="fact_business_activity",
                grain="one row per tenant, date, team, customer, product, and activity type",
                description="业务活动事实表，覆盖拜访、会议、内容触达和商机。",
                foreign_keys={
                    "date_id": "dim_date",
                    "team_id": "dim_team",
                    "customer_id": "dim_customer",
                    "product_id": "dim_product",
                },
                degenerate_dimensions=(
                    WarehouseColumn("activity_id", "TEXT", nullable=False),
                    WarehouseColumn("activity_type", "TEXT", nullable=False),
                ),
                measures=(
                    WarehouseColumn("visit_count", "INTEGER", nullable=False),
                    WarehouseColumn("engagement_score", "REAL", nullable=False),
                    WarehouseColumn("opportunity_amount", "REAL", nullable=False),
                    WarehouseColumn("compliance_issue_count", "INTEGER", nullable=False),
                ),
            )
        }

    def tables(self) -> dict[str, DimensionTable | FactTable]:
        return {**self.dimensions, **self.facts}

    def ddl(self) -> list[str]:
        return [table.ddl() for table in self.tables().values()]

    def describe(self) -> dict[str, Any]:
        return {
            "dimensions": {name: table.description for name, table in self.dimensions.items()},
            "facts": {
                name: {
                    "grain": table.grain,
                    "description": table.description,
                    "measures": [measure.name for measure in table.measures],
                }
                for name, table in self.facts.items()
            },
        }


DEFAULT_STAR_SCHEMA = StarSchema()
