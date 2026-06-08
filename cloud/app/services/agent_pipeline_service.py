"""Agent 流水线服务，管理多步骤流水线的创建、执行与运行记录。"""

import json
from datetime import datetime

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    AgentPipelinesRepository,
    PipelineRunsRepository,
    PipelineStepRunsRepository,
    PipelineStepsRepository,
)
from cloud.app.services.base import BaseService
from cloud.app.services.pipeline_executor import PipelineExecutorMixin
from shared.base import PaginatedResponse, success


class AgentPipelineService(PipelineExecutorMixin, BaseService):
    """AgentPipeline 服务，提供流水线 CRUD、运行与执行记录查询。"""

    @staticmethod
    def _pd(row) -> dict:
        """将流水线数据库行转为标准字典。

        Args:
            row: 数据库行或字典

        Returns:
            流水线基本信息字典
        """
        return {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "is_active": row["is_active"],
            "created_by": row["created_by"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def _sd(row) -> dict:
        """将步骤数据库行转为标准字典。

        Args:
            row: 数据库行或字典

        Returns:
            步骤基本信息字典
        """
        return {
            "id": row["id"],
            "pipeline_id": row["pipeline_id"],
            "step_order": row["step_order"],
            "agent_role_id": row["agent_role_id"],
            "input_mapping": row["input_mapping"],
            "custom_prompt_override": row["custom_prompt_override"],
            "created_at": row["created_at"],
        }

    def _p404(self, pid: int):
        """按流水线 ID 获取记录，不存在则抛出 404。

        Args:
            pid: 流水线 ID

        Returns:
            流水线记录字典

        Raises:
            HTTPException: 流水线不存在时返回 404
        """
        repo = AgentPipelinesRepository(self.db)
        row = repo.get_by_id(pid)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
        return row

    def create_pipeline(self, body, uid: int) -> dict:
        """创建流水线及其步骤。

        Args:
            body: 请求体（含 name、description、steps）
            uid: 创建者 ID

        Returns:
            创建的流水线记录
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pipelines_repo = AgentPipelinesRepository(self.db)
        steps_repo = PipelineStepsRepository(self.db)
        pid = pipelines_repo.create(
            {
                "name": body.name,
                "description": body.description,
                "created_by": uid,
                "created_at": now,
                "updated_at": now,
            }
        )
        for s in body.steps:
            steps_repo.create(
                {
                    "pipeline_id": pid,
                    "step_order": s.step_order,
                    "agent_role_id": s.agent_role_id,
                    "input_mapping": json.dumps(s.input_mapping, ensure_ascii=False),
                    "custom_prompt_override": s.custom_prompt_override,
                }
            )
        return success(data=self._pd(pipelines_repo.get_by_id(pid)))

    def list_pipelines(self) -> dict:
        """列出所有流水线（含步骤数）。

        Returns:
            流水线列表
        """
        pipelines_repo = AgentPipelinesRepository(self.db)
        steps_repo = PipelineStepsRepository(self.db)
        rows = pipelines_repo.list_all(order_by="created_at DESC")
        result = []
        for r in rows:
            step_count = steps_repo.count(conditions=["pipeline_id=?"], params=[r["id"]])
            result.append({**self._pd(r), "step_count": step_count})
        return success(data=result)

    def get_pipeline(self, pipeline_id: int) -> dict:
        """获取流水线详情（含步骤列表）。

        Args:
            pipeline_id: 流水线 ID

        Returns:
            流水线记录含步骤
        """
        steps_repo = PipelineStepsRepository(self.db)
        row = self._p404(pipeline_id)
        steps = steps_repo.list_all(conditions=["pipeline_id=?"], params=[pipeline_id], order_by="step_order ASC")
        return success(data={**self._pd(row), "steps": [self._sd(s) for s in steps]})

    def delete_pipeline(self, pipeline_id: int) -> dict:
        """删除流水线及其关联的步骤和运行记录。

        Args:
            pipeline_id: 流水线 ID

        Returns:
            成功响应
        """
        pipelines_repo = AgentPipelinesRepository(self.db)
        steps_repo = PipelineStepsRepository(self.db)
        runs_repo = PipelineRunsRepository(self.db)
        self._p404(pipeline_id)
        for step in steps_repo.list_all(conditions=["pipeline_id=?"], params=[pipeline_id]):
            steps_repo.delete(step["id"])
        for run in runs_repo.list_all(conditions=["pipeline_id=?"], params=[pipeline_id]):
            runs_repo.delete(run["id"])
        pipelines_repo.delete(pipeline_id)
        return success()

    def get_run(self, run_id: int) -> dict:
        """获取运行记录及步骤执行结果。

        Args:
            run_id: 运行 ID

        Returns:
            含 run 和 step_runs 的记录
        """
        runs_repo = PipelineRunsRepository(self.db)
        step_runs_repo = PipelineStepRunsRepository(self.db)
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
        """分页查询流水线运行记录。

        Args:
            pipeline_id: 流水线 ID
            page: 页码
            page_size: 每页条数

        Returns:
            分页运行记录
        """
        runs_repo = PipelineRunsRepository(self.db)
        self._p404(pipeline_id)
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
