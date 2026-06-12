"""Agent 流水线执行方法。"""

import json
from datetime import datetime
from typing import Any

from fastapi import HTTPException, Request
from starlette import status

from cloud.app.repositories import PipelineRunsRepository, PipelineStepRunsRepository
from cloud.lg_utils.pipeline_graph import get_pipeline_graph
from shared.base import success


class PipelineExecutorMixin:
    """流水线运行创建、LangGraph 执行和步骤结果落库方法。"""

    db: Any
    _p404: Any

    def run_pipeline(self, pipeline_id: int, body, request: Request, uid: int) -> dict:
        """执行流水线，通过 LangGraph 编排多步骤 Agent。

        Args:
            pipeline_id: 流水线 ID
            body: 请求体（含 user_input）
            request: HTTP 请求对象（用于传递 Authorization）
            uid: 执行者 ID

        Returns:
            含 run_id、status 和 step_results 的执行结果
        """
        runs_repo = PipelineRunsRepository(self._connection())
        step_runs_repo = PipelineStepRunsRepository(self._connection())

        self._p404(pipeline_id)
        steps = self.db.execute(
            "SELECT ps.*, ar.system_prompt, ar.name AS ar_name, ar.temperature, ar.max_tokens "
            "FROM pipeline_steps ps JOIN agent_roles ar ON ps.agent_role_id=ar.id "
            "WHERE ps.pipeline_id=? ORDER BY ps.step_order",
            (pipeline_id,),
        ).fetchall()
        if not steps:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Pipeline has no steps")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        run_id = runs_repo.create(
            {
                "pipeline_id": pipeline_id,
                "user_input": body.user_input,
                "status": "running",
                "started_at": now,
                "created_by": uid,
            }
        )

        auth_header = request.headers.get("Authorization", "")
        graph_steps = []
        for step in steps:
            graph_steps.append(
                {
                    "step_order": step["step_order"],
                    "agent_role_id": step["agent_role_id"],
                    "agent_name": step["ar_name"],
                    "system_prompt": step["system_prompt"],
                    "custom_prompt_override": step["custom_prompt_override"],
                    "temperature": step["temperature"] or 0.7,
                    "max_tokens": step["max_tokens"] or 2048,
                    "input_mapping": json.loads(step["input_mapping"]) if step["input_mapping"] else {},
                }
            )

        initial_state = {
            "steps": graph_steps,
            "current_index": 0,
            "accumulated_outputs": [],
            "current_step_input": None,
            "done": False,
            "auth_header": auth_header,
            "previous_output": "",
            "user_input": body.user_input,
        }

        graph = get_pipeline_graph()
        result = graph.invoke(initial_state)

        step_results = result["accumulated_outputs"]
        final_status = "completed"
        for sr in step_results:
            s_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            matching_step = next((s for s in steps if s["step_order"] == sr["step_order"]), None)
            step_runs_repo.create(
                {
                    "run_id": run_id,
                    "step_order": sr["step_order"],
                    "agent_role_id": matching_step["agent_role_id"] if matching_step else 0,
                    "agent_role_name": sr["agent_name"],
                    "input_data": json.dumps(sr.get("messages", []), ensure_ascii=False),
                    "output_data": sr["output"],
                    "ai_response_raw": sr["output"] if sr["status"] == "completed" else "",
                    "tokens_used": sr.get("tokens", 0),
                    "status": sr["status"],
                    "started_at": s_now,
                    "completed_at": s_now,
                }
            )
            if sr["status"] == "failed":
                final_status = "failed"

        c_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        runs_repo.update(
            run_id,
            {
                "status": final_status,
                "result": json.dumps({"steps": step_results}, ensure_ascii=False),
                "completed_at": c_now,
            },
        )
        return success(data={"run_id": run_id, "status": final_status, "steps": step_results})
