"""Agent 流水线执行调度模块，追踪运行与步骤执行结果。"""

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import PipelineRunsRepository, PipelineStepRunsRepository
from shared.base import PaginatedResponse, success


class PipelineRunQueryMixin:
    """流水线运行查询混入类，提供运行记录查询与分页。"""

    def get_run(self, run_id: int) -> dict:
        runs_repo = PipelineRunsRepository(self._connection())
        step_runs_repo = PipelineStepRunsRepository(self._connection())
        row = runs_repo.get_by_id(run_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Run not found")
        steps = step_runs_repo.list_all(conditions=["run_id=?"], params=[run_id], order_by="step_order ASC")
        return success(
            data={
                "run": dict(row),
                "step_runs": steps,
            }
        )

    def list_runs(self, pipeline_id: int, page: int, page_size: int) -> dict:
        runs_repo = PipelineRunsRepository(self._connection())
        total, total_pages, rows = runs_repo.paginate(
            page=page,
            page_size=page_size,
            conditions=["pipeline_id=?"],
            params=[pipeline_id],
            order_by="started_at DESC",
        )
        return success(
            data=PaginatedResponse(
                items=rows,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )
        )
