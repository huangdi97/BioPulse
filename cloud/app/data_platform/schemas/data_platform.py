"""数据中台 Pydantic 模型。"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PipelineRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class DataSourceType(str, Enum):
    DATABASE = "database"
    API = "api"
    FILE = "file"
    STREAM = "stream"


class MetricAggregation(str, Enum):
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    MIN = "min"
    MAX = "max"


class DataSourceConfig(BaseModel):
    name: str
    type: DataSourceType = DataSourceType.DATABASE
    uri: str = ""
    table: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class TransformationSpec(BaseModel):
    name: str
    sql: str
    materialized: str = "view"
    depends_on: list[str] = Field(default_factory=list)


class PipelineTask(BaseModel):
    id: str
    name: str
    upstream: list[str] = Field(default_factory=list)
    retries: int = Field(default=0, ge=0)
    timeout_seconds: int | None = Field(default=None, gt=0)


class PipelineRunResult(BaseModel):
    run_id: str
    pipeline_name: str
    status: PipelineRunStatus
    processed_rows: int = Field(default=0, ge=0)
    task_results: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


class OLAPQuery(BaseModel):
    dimensions: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)
    date_from: str | None = None
    date_to: str | None = None
    limit: int = Field(default=100, gt=0, le=10000)


class BIReportRequest(BaseModel):
    date_from: str | None = None
    date_to: str | None = None
    team_id: str | None = None
    metrics: list[str] = Field(default_factory=list)
    group_by: list[str] = Field(default_factory=lambda: ["activity_date", "team_id"])
