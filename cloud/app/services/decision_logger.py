"""决策日志服务，负责决策案例与流水线运行的记录与查询。"""

import json
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    CrossCaseInsightsRepository,
    DecisionCasesRepository,
    PipelineRunsRepository,
    PipelineStepRunsRepository,
)
from cloud.app.services.decision_report import DecisionReportMixin
from shared.base import validate_columns
from shared.base_service import BaseService
from shared.columns import TABLE_CROSS_CASE_INSIGHTS_COLS, TABLE_DECISION_CASES_COLS
from shared.datetime_utils import now as _now


def _e404(name: str = "Resource"):
    raise HTTPException(status.HTTP_404_NOT_FOUND, f"{name} not found")


class DecisionLogger(DecisionReportMixin, BaseService):
    """决策日志服务，记录决策案例、流水线运行与跨案例洞察。"""

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
        """创建一条决策案例。"""
        ctx = context
        if pipeline_run_id:
            run_repo = PipelineRunsRepository(self._connection())
            run = run_repo.get_by_id(pipeline_run_id)
            if run:
                step_repo = PipelineStepRunsRepository(self._connection())
                steps = step_repo.list_all(
                    conditions=["run_id=?"],
                    params=[pipeline_run_id],
                    order_by="step_order",
                )
                ctx = {**ctx, "pipeline_run": run, "step_runs": steps}
        case_repo = DecisionCasesRepository(self._connection())
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
        """分页列出决策案例，支持分数范围 / 标签 / 关键词筛选。"""
        case_repo = DecisionCasesRepository(self._connection())
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
        """根据 ID 获取单个决策案例，不存在则 404。"""
        row = DecisionCasesRepository(self._connection()).get_active_by_id(case_id)
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
        """更新决策案例的指定字段，不传的字段保持不变。"""
        case_repo = DecisionCasesRepository(self._connection())
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
        """软删除指定决策案例及其关联数据。"""
        case_repo = DecisionCasesRepository(self._connection())
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
        """分页列出跨案例洞察，支持类型 / 置信度筛选。"""
        total, total_pages, items = CrossCaseInsightsRepository(self._connection()).list_filtered(
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
        """根据 ID 获取单个洞察，不存在则 404。"""
        row = CrossCaseInsightsRepository(self._connection()).get_active_by_id(insight_id)
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
        """更新洞察的指定字段，不传的字段保持不变。"""
        repo = CrossCaseInsightsRepository(self._connection())
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
