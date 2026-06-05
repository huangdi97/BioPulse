import json
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    CausalAnalysesRepository,
    CrossCaseInsightsRepository,
    DecisionCasesRepository,
    PipelineRunsRepository,
    PipelineStepRunsRepository,
)
from cloud.app.services.base import BaseService
from shared.base import validate_columns
from shared.columns import TABLE_CROSS_CASE_INSIGHTS_COLS, TABLE_DECISION_CASES_COLS


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _e404(name: str = "Resource"):
    raise HTTPException(status.HTTP_404_NOT_FOUND, f"{name} not found")


class DecisionLogger(BaseService):
    def create_case(
        self,
        name: str,
        pipeline_run_id: Optional[int],
        description: str,
        outcome: str,
        outcome_score: float,
        context: dict,
        tags: list,
        uid: int,
    ) -> dict:
        ctx = context
        if pipeline_run_id:
            run_repo = PipelineRunsRepository(self.db)
            run = run_repo.get_by_id(pipeline_run_id)
            if run:
                step_repo = PipelineStepRunsRepository(self.db)
                steps = step_repo.list_all(
                    conditions=["run_id=?"],
                    params=[pipeline_run_id],
                    order_by="step_order",
                )
                ctx = {**ctx, "pipeline_run": run, "step_runs": steps}
        case_repo = DecisionCasesRepository(self.db)
        case_id = case_repo.create(
            {
                "name": name,
                "pipeline_run_id": pipeline_run_id,
                "description": description,
                "outcome": outcome,
                "outcome_score": outcome_score,
                "context": json.dumps(ctx, ensure_ascii=False),
                "tags": json.dumps(tags, ensure_ascii=False),
                "created_by": uid,
                "created_at": _now(),
                "updated_at": _now(),
            }
        )
        return case_repo.get_by_id(case_id)

    def list_cases(
        self,
        outcome_score_min: Optional[float] = None,
        outcome_score_max: Optional[float] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        case_repo = DecisionCasesRepository(self.db)
        total, total_pages, items = case_repo.list_filtered(
            outcome_score_min=outcome_score_min,
            outcome_score_max=outcome_score_max,
            tag=tag,
            search=search,
            page=page,
            page_size=page_size,
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_case(self, case_id: int) -> dict:
        row = DecisionCasesRepository(self.db).get_active_by_id(case_id)
        if not row:
            _e404("Case")
        return row

    def update_case(
        self,
        case_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        outcome: Optional[str] = None,
        outcome_score: Optional[float] = None,
        context: Optional[dict] = None,
        tags: Optional[list] = None,
    ) -> dict:
        case_repo = DecisionCasesRepository(self.db)
        row = case_repo.get_active_by_id(case_id)
        if not row:
            _e404("Case")
        updates = {}
        for f in ("name", "description", "outcome", "outcome_score"):
            v = locals().get(f)
            if v is not None:
                updates[f] = v
        if context is not None:
            updates["context"] = json.dumps(context, ensure_ascii=False)
        if tags is not None:
            updates["tags"] = json.dumps(tags, ensure_ascii=False)
        if updates:
            updates["updated_at"] = _now()
            validate_columns(updates, "decision_cases", TABLE_DECISION_CASES_COLS)
            case_repo.update(case_id, updates)
        return case_repo.get_by_id(case_id)

    def delete_case(self, case_id: int) -> None:
        case_repo = DecisionCasesRepository(self.db)
        row = case_repo.get_active_by_id(case_id)
        if not row:
            _e404("Case")
        case_repo.soft_delete_with_causal(case_id)

    def list_insights(
        self,
        insight_type: Optional[str] = None,
        confidence_min: Optional[float] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        total, total_pages, items = CrossCaseInsightsRepository(self.db).list_filtered(
            insight_type=insight_type,
            confidence_min=confidence_min,
            page=page,
            page_size=page_size,
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_insight(self, insight_id: int) -> dict:
        row = CrossCaseInsightsRepository(self.db).get_active_by_id(insight_id)
        if not row:
            _e404("Insight")
        return row

    def update_insight(
        self,
        insight_id: int,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        confidence: Optional[float] = None,
        applicability: Optional[str] = None,
    ) -> dict:
        repo = CrossCaseInsightsRepository(self.db)
        row = repo.get_active_by_id(insight_id)
        if not row:
            _e404("Insight")
        updates = {}
        for f in ("title", "summary", "confidence", "applicability"):
            v = locals().get(f)
            if v is not None:
                updates[f] = v
        if updates:
            updates["updated_at"] = _now()
            validate_columns(updates, "cross_case_insights", TABLE_CROSS_CASE_INSIGHTS_COLS)
            repo.update(insight_id, updates)
        return repo.get_by_id(insight_id)

    def dashboard(self) -> dict:
        case_repo = DecisionCasesRepository(self.db)
        analysis_repo = CausalAnalysesRepository(self.db)
        insight_repo = CrossCaseInsightsRepository(self.db)
        total_cases = case_repo.count_active()
        analyzed = analysis_repo.count_distinct_case_ids()
        score_dist = case_repo.score_distribution()
        insight_counts = insight_repo.count_by_type()
        top_insights = insight_repo.top_by_confidence(5)
        return {
            "total_cases": total_cases,
            "analyzed_cases": analyzed,
            "score_distribution": score_dist,
            "insights_by_type": insight_counts,
            "top_insights": top_insights,
        }
