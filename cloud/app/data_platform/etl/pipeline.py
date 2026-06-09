"""Simplified Airflow-style ETL pipeline definitions."""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Iterable
from uuid import uuid4

from cloud.app.data_platform.etl.transformations import DEFAULT_TRANSFORMATIONS, SQLModel
from cloud.app.data_platform.schemas.data_platform import PipelineRunResult, PipelineRunStatus

Extractor = Callable[[], list[dict[str, Any]]]
Transformer = Callable[[list[dict[str, Any]]], list[dict[str, Any]]]
Loader = Callable[[list[dict[str, Any]]], int]


@dataclass
class ETLTask:
    id: str
    name: str
    action: Callable[[dict[str, Any]], dict[str, Any]]
    upstream: list[str] = field(default_factory=list)
    retries: int = 0


class ETLPipeline:
    """Data source to ETL workflow, modeled after Airflow DAG concepts."""

    def __init__(self, name: str = "default_data_platform_pipeline") -> None:
        self.name = name
        self.tasks: dict[str, ETLTask] = {}
        self.transformations: list[SQLModel] = list(DEFAULT_TRANSFORMATIONS)
        self._sources: dict[str, Extractor] = {}
        self._loaders: dict[str, Loader] = {}

    def add_source(self, name: str, extractor: Extractor) -> None:
        self._sources[name] = extractor

    def add_loader(self, name: str, loader: Loader) -> None:
        self._loaders[name] = loader

    def add_task(
        self,
        task_id: str,
        name: str,
        action: Callable[[dict[str, Any]], dict[str, Any]],
        upstream: Iterable[str] | None = None,
        retries: int = 0,
    ) -> None:
        self.tasks[task_id] = ETLTask(
            id=task_id,
            name=name,
            action=action,
            upstream=list(upstream or []),
            retries=retries,
        )

    def define_standard_pipeline(
        self,
        source_name: str = "crm",
        loader_name: str = "warehouse",
        transformer: Transformer | None = None,
    ) -> None:
        transformer = transformer or self._default_transform

        def extract(context: dict[str, Any]) -> dict[str, Any]:
            extractor = self._sources.get(source_name, self._sample_extract)
            rows = extractor()
            return {**context, "rows": rows, "processed_rows": len(rows)}

        def transform(context: dict[str, Any]) -> dict[str, Any]:
            rows = transformer(context.get("rows", []))
            return {**context, "rows": rows, "processed_rows": len(rows)}

        def load(context: dict[str, Any]) -> dict[str, Any]:
            loader = self._loaders.get(loader_name, lambda rows: len(rows))
            loaded = loader(context.get("rows", []))
            return {**context, "loaded_rows": loaded}

        self.add_task("extract", "Extract from data source", extract)
        self.add_task("transform", "Apply dbt-style transformations", transform, upstream=["extract"])
        self.add_task("load", "Load into warehouse", load, upstream=["transform"])

    def compile_sql_transformations(self) -> list[str]:
        return [transformation.compile() for transformation in self.transformations]

    def run(self, context: dict[str, Any] | None = None) -> PipelineRunResult:
        if not self.tasks:
            self.define_standard_pipeline()

        run_id = f"etl-{uuid4().hex[:10]}"
        task_results: list[dict[str, Any]] = []
        current_context = {
            "run_id": run_id,
            "pipeline_name": self.name,
            "started_at": datetime.now().isoformat(timespec="seconds"),
            **(context or {}),
        }

        try:
            for task_id in self._topological_order():
                task = self.tasks[task_id]
                attempts = 0
                while True:
                    try:
                        current_context = task.action(current_context)
                        task_results.append({"task_id": task.id, "name": task.name, "status": "success"})
                        break
                    except Exception as exc:
                        attempts += 1
                        if attempts > task.retries:
                            raise RuntimeError(f"Task {task.id} failed: {exc}") from exc
            return PipelineRunResult(
                run_id=run_id,
                pipeline_name=self.name,
                status=PipelineRunStatus.SUCCESS,
                processed_rows=int(current_context.get("processed_rows", 0)),
                task_results=task_results,
            )
        except Exception as exc:
            return PipelineRunResult(
                run_id=run_id,
                pipeline_name=self.name,
                status=PipelineRunStatus.FAILED,
                processed_rows=int(current_context.get("processed_rows", 0)),
                task_results=task_results,
                error=str(exc),
            )

    def _topological_order(self) -> list[str]:
        indegree = {task_id: 0 for task_id in self.tasks}
        children: dict[str, list[str]] = defaultdict(list)
        for task_id, task in self.tasks.items():
            for parent in task.upstream:
                if parent not in self.tasks:
                    raise ValueError(f"Unknown upstream task: {parent}")
                indegree[task_id] += 1
                children[parent].append(task_id)

        queue = deque(task_id for task_id, degree in indegree.items() if degree == 0)
        ordered: list[str] = []
        while queue:
            task_id = queue.popleft()
            ordered.append(task_id)
            for child in children[task_id]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)

        if len(ordered) != len(self.tasks):
            raise ValueError("Pipeline tasks contain a dependency cycle")
        return ordered

    @staticmethod
    def _default_transform(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        transformed = []
        for row in rows:
            normalized = dict(row)
            normalized.setdefault("tenant_id", "default")
            normalized.setdefault("visit_count", 0)
            normalized.setdefault("engagement_score", 0.0)
            normalized.setdefault("opportunity_amount", 0.0)
            normalized.setdefault("compliance_issue_count", 0)
            transformed.append(normalized)
        return transformed

    @staticmethod
    def _sample_extract() -> list[dict[str, Any]]:
        return [
            {
                "tenant_id": "tenant-demo",
                "activity_id": "act-001",
                "activity_date": "2026-06-09",
                "team_id": "team-east",
                "customer_id": "hcp-001",
                "product_id": "prod-001",
                "activity_type": "visit",
                "visit_count": 1,
                "engagement_score": 82.5,
                "opportunity_amount": 12000.0,
                "compliance_issue_count": 0,
            }
        ]
