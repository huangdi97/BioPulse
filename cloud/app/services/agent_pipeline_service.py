"""Agent 流水线服务，管理多步骤流水线的创建、执行与运行记录。"""

import json
from datetime import datetime

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    AgentPipelinesRepository,
    PipelineStepsRepository,
)
from cloud.app.services.agent_pipeline_exec import PipelineRunQueryMixin
from cloud.app.services.pipeline_executor import PipelineExecutorMixin
from shared.base import ApiResponse, success
from shared.base_service import BaseService


class AgentPipelineService(PipelineRunQueryMixin, PipelineExecutorMixin, BaseService):
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

    def create_pipeline(self, body, uid: int) -> ApiResponse:
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

    def list_pipelines(self) -> ApiResponse:
        """列出所有流水线（含步骤数）。

        Returns:
            流水线列表
        """
        pipelines_repo = AgentPipelinesRepository(self.db)
        rows = pipelines_repo.list_all(order_by="created_at DESC")
        pipeline_ids = [r["id"] for r in rows]
        step_counts = {}
        if pipeline_ids:
            placeholders = ",".join("?" * len(pipeline_ids))
            count_rows = self.db.execute(
                f"SELECT pipeline_id, COUNT(*) AS cnt FROM pipeline_steps WHERE pipeline_id IN ({placeholders}) GROUP BY pipeline_id",
                pipeline_ids,
            ).fetchall()
            step_counts = {r["pipeline_id"]: r["cnt"] for r in count_rows}
        result = [{**self._pd(r), "step_count": step_counts.get(r["id"], 0)} for r in rows]
        return success(data=result)

    def get_pipeline(self, pipeline_id: int) -> ApiResponse:
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

    def delete_pipeline(self, pipeline_id: int) -> ApiResponse:
        """删除流水线及其关联的步骤和运行记录。

        Args:
            pipeline_id: 流水线 ID

        Returns:
            成功响应
        """
        pipelines_repo = AgentPipelinesRepository(self.db)
        self._p404(pipeline_id)
        self.db.execute("DELETE FROM pipeline_steps WHERE pipeline_id=?", (pipeline_id,))
        self.db.execute("DELETE FROM pipeline_runs WHERE pipeline_id=?", (pipeline_id,))
        pipelines_repo.delete(pipeline_id)
        return success()
