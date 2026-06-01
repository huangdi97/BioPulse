import json
import urllib.error
import urllib.request
from datetime import datetime

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    AgentPipelinesRepository, PipelineStepsRepository,
    PipelineRunsRepository, PipelineStepRunsRepository,
)
from cloud.app.services.base import BaseService
from shared.base import PaginatedResponse


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def pd(row) -> dict:
    return {"id": row["id"], "name": row["name"], "description": row["description"],
            "is_active": row["is_active"], "created_by": row["created_by"],
            "created_at": row["created_at"], "updated_at": row["updated_at"]}


def sd(row) -> dict:
    return {"id": row["id"], "pipeline_id": row["pipeline_id"],
            "step_order": row["step_order"], "agent_role_id": row["agent_role_id"],
            "input_mapping": row["input_mapping"],
            "custom_prompt_override": row["custom_prompt_override"],
            "created_at": row["created_at"]}


class AgentPipelineService(BaseService):
    def _get_pipeline_or_404(self, pipeline_id: int) -> dict:
        pipelines_repo = AgentPipelinesRepository(self.db)
        row = pipelines_repo.get_by_id(pipeline_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
        return row

    def create_pipeline(self, name: str, description: str,
                        steps: list, user_id: int) -> dict:
        now = _now()
        pipelines_repo = AgentPipelinesRepository(self.db)
        steps_repo = PipelineStepsRepository(self.db)
        pid = pipelines_repo.create({
            "name": name, "description": description,
            "created_by": user_id, "created_at": now, "updated_at": now,
        })
        for s in steps:
            steps_repo.create({
                "pipeline_id": pid, "step_order": s["step_order"],
                "agent_role_id": s["agent_role_id"],
                "input_mapping": s.get("input_mapping"),
                "custom_prompt_override": s.get("custom_prompt_override", ""),
            })
        return pd(pipelines_repo.get_by_id(pid))

    def list_pipelines(self) -> list:
        pipelines_repo = AgentPipelinesRepository(self.db)
        steps_repo = PipelineStepsRepository(self.db)
        rows = pipelines_repo.list_all(order_by="created_at DESC")
        result = []
        for r in rows:
            step_count = steps_repo.count(conditions=["pipeline_id=?"], params=[r["id"]])
            result.append({**pd(r), "step_count": step_count})
        return result

    def get_pipeline(self, pipeline_id: int) -> dict:
        pipelines_repo = AgentPipelinesRepository(self.db)
        steps_repo = PipelineStepsRepository(self.db)
        row = self._get_pipeline_or_404(pipeline_id)
        steps = steps_repo.list_all(
            conditions=["pipeline_id=?"], params=[pipeline_id], order_by="step_order ASC"
        )
        return {**pd(row), "steps": [sd(s) for s in steps]}

    def delete_pipeline(self, pipeline_id: int) -> None:
        pipelines_repo = AgentPipelinesRepository(self.db)
        steps_repo = PipelineStepsRepository(self.db)
        runs_repo = PipelineRunsRepository(self.db)
        self._get_pipeline_or_404(pipeline_id)
        for step in steps_repo.list_all(conditions=["pipeline_id=?"], params=[pipeline_id]):
            steps_repo.delete(step["id"])
        for run in runs_repo.list_all(conditions=["pipeline_id=?"], params=[pipeline_id]):
            runs_repo.delete(run["id"])
        pipelines_repo.delete(pipeline_id)

    def run_pipeline(self, pipeline_id: int, user_input: str,
                     auth_header: str, user_id: int) -> dict:
        pipelines_repo = AgentPipelinesRepository(self.db)
        steps_repo = PipelineStepsRepository(self.db)
        runs_repo = PipelineRunsRepository(self.db)
        step_runs_repo = PipelineStepRunsRepository(self.db)

        pipeline = self._get_pipeline_or_404(pipeline_id)
        steps = self.db.execute(
            "SELECT ps.*, ar.system_prompt, ar.name AS ar_name, ar.temperature, ar.max_tokens "
            "FROM pipeline_steps ps JOIN agent_roles ar ON ps.agent_role_id=ar.id "
            "WHERE ps.pipeline_id=? ORDER BY ps.step_order", (pipeline_id,)).fetchall()
        if not steps:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Pipeline has no steps")
        now = _now()
        run_id = runs_repo.create({
            "pipeline_id": pipeline_id, "user_input": user_input,
            "status": "running", "started_at": now, "created_by": user_id,
        })

        previous_output = ""
        final_status = "completed"
        step_results = []

        for step in steps:
            s_now = _now()
            input_mapping = json.loads(step["input_mapping"]) if step["input_mapping"] else {}
            user_content = user_input
            if input_mapping.get("user_input") == "$request":
                user_content = user_input
            ctx = input_mapping.get("context", "")
            strategy = input_mapping.get("strategy", "")
            if previous_output:
                if ctx == "previous_output":
                    user_content = previous_output
                if strategy == "previous_output":
                    user_content = previous_output
                if not input_mapping:
                    user_content = previous_output

            messages = [
                {"role": "system", "content": step["custom_prompt_override"] or step["system_prompt"]},
                {"role": "user", "content": user_content},
            ]
            sr_id = step_runs_repo.create({
                "run_id": run_id, "step_order": step["step_order"],
                "agent_role_id": step["agent_role_id"], "agent_role_name": step["ar_name"],
                "input_data": json.dumps(messages, ensure_ascii=False),
                "status": "running", "started_at": s_now,
            })

            step_status = "completed"
            output_data = ""
            ai_raw = ""
            tokens = 0
            try:
                payload = {
                    "messages": messages,
                    "temperature": step["temperature"] or 0.7,
                    "max_tokens": step["max_tokens"] or 2048,
                }
                req = urllib.request.Request(
                    "http://localhost:8000/ai/chat",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "Authorization": auth_header},
                    method="POST")
                with urllib.request.urlopen(req, timeout=120) as rp:
                    resp = json.loads(rp.read().decode("utf-8"))
                    ai_raw = resp.get("data", {}).get("reply", "")
                    usage = resp.get("data", {}).get("usage", {})
                    tokens = usage.get("total_tokens", 0) if usage else 0
                    output_data = ai_raw
            except Exception as e:
                step_status = "failed"
                output_data = str(e)
                final_status = "failed"

            c_now = _now()
            step_runs_repo.update(sr_id, {
                "output_data": output_data, "ai_response_raw": ai_raw,
                "tokens_used": tokens, "status": step_status, "completed_at": c_now,
            })
            step_results.append({
                "step_order": step["step_order"], "agent_name": step["ar_name"],
                "output": output_data, "status": step_status,
            })
            previous_output = output_data
            if step_status == "failed":
                break

        c_now = _now()
        runs_repo.update(run_id, {
            "status": final_status,
            "result": json.dumps({"steps": step_results}, ensure_ascii=False),
            "completed_at": c_now,
        })
        return {"run_id": run_id, "status": final_status, "steps": step_results}

    def get_run(self, run_id: int) -> dict:
        runs_repo = PipelineRunsRepository(self.db)
        step_runs_repo = PipelineStepRunsRepository(self.db)
        row = runs_repo.get_by_id(run_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Run not found")
        steps = step_runs_repo.list_all(
            conditions=["run_id=?"], params=[run_id], order_by="step_order ASC"
        )
        return {"run": dict(row), "step_runs": steps}

    def list_runs(self, pipeline_id: int, page: int, page_size: int) -> dict:
        pipelines_repo = AgentPipelinesRepository(self.db)
        runs_repo = PipelineRunsRepository(self.db)
        self._get_pipeline_or_404(pipeline_id)
        total, total_pages, rows = runs_repo.paginate(
            page=page, page_size=page_size,
            conditions=["pipeline_id=?"], params=[pipeline_id],
            order_by="started_at DESC",
        )
        return PaginatedResponse(
            items=rows, total=total, page=page,
            page_size=page_size, total_pages=total_pages,
        )
