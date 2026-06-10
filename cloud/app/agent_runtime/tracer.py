"""Agent 执行追踪 — 记录每条 trace 的完整链路、工具调用和 LLM 消耗。"""

import json
import logging
import time
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentTracer:
    """Agent 执行追踪器，记录 trace 的完整生命周期。"""

    def __init__(self, db):
        self._db = db
        self.current_trace: str | None = None
        self._start_time: float = 0.0
        self._tool_calls: list[dict] = []
        self._llm_calls: list[dict] = []
        self._agent_name: str = ""
        self._user_id: str = ""
        self._input_data: dict = {}

    def start_trace(self, agent_name: str, user_id: str, input_data: dict) -> str:
        trace_id = str(uuid.uuid4())
        self.current_trace = trace_id
        self._start_time = time.time()
        self._agent_name = agent_name
        self._user_id = user_id
        self._input_data = input_data
        self._tool_calls = []
        self._llm_calls = []
        logger.info("Trace started: %s agent=%s", trace_id, agent_name)
        return trace_id

    def log_tool_call(self, tool_name: str, args: dict, result: str, duration_ms: int) -> None:
        entry = {
            "tool_name": tool_name,
            "args": args,
            "result_preview": result[:500] if result else "",
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
        }
        self._tool_calls.append(entry)

    def log_llm_call(self, model: str, prompt_tokens: int, completion_tokens: int, duration_ms: int) -> None:
        entry = {
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
        }
        self._llm_calls.append(entry)

    def end_trace(self, status: str, output: dict) -> None:
        if not self.current_trace:
            return
        total_duration = int((time.time() - self._start_time) * 1000)
        total_prompt = sum(c.get("prompt_tokens", 0) for c in self._llm_calls)
        total_completion = sum(c.get("completion_tokens", 0) for c in self._llm_calls)
        try:
            self._db.execute(
                "INSERT INTO agent_traces "
                "(trace_id, agent_name, user_id, input_data, output_data, status, "
                "total_duration_ms, total_prompt_tokens, total_completion_tokens, "
                "tool_calls_json, llm_calls_json, started_at, ended_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    self.current_trace,
                    self._agent_name,
                    self._user_id,
                    json.dumps(self._input_data, ensure_ascii=False),
                    json.dumps(output, ensure_ascii=False),
                    status,
                    total_duration,
                    total_prompt,
                    total_completion,
                    json.dumps(self._tool_calls, ensure_ascii=False),
                    json.dumps(self._llm_calls, ensure_ascii=False),
                    datetime.fromtimestamp(self._start_time).isoformat(),
                    datetime.now().isoformat(),
                ),
            )
            self._db.commit()
        except Exception:
            logger.exception("Failed to save trace %s", self.current_trace)
        logger.info(
            "Trace ended: %s status=%s duration=%dms tokens=%d",
            self.current_trace,
            status,
            total_duration,
            total_prompt + total_completion,
        )
        self.current_trace = None

    def get_trace(self, trace_id: str) -> dict | None:
        row = self._db.execute("SELECT * FROM agent_traces WHERE trace_id=?", (trace_id,)).fetchone()
        if not row:
            return None
        return dict(row)

    def list_traces(self, agent_name: str | None = None, user_id: str | None = None, page: int = 1, page_size: int = 20) -> dict:
        conditions = []
        params = []
        if agent_name:
            conditions.append("agent_name = ?")
            params.append(agent_name)
        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)
        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        offset = (page - 1) * page_size
        total = self._db.execute(f"SELECT COUNT(*) as cnt FROM agent_traces{where}", params).fetchone()["cnt"]
        rows = self._db.execute(
            f"SELECT * FROM agent_traces{where} ORDER BY started_at DESC LIMIT ? OFFSET ?",
            params + [page_size, offset],
        ).fetchall()
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [dict(r) for r in rows],
        }

    def get_metrics_summary(self) -> dict:
        row = self._db.execute(
            "SELECT "
            "COUNT(*) as total_runs, "
            "AVG(total_duration_ms) as avg_duration_ms, "
            "SUM(total_prompt_tokens + total_completion_tokens) as total_tokens, "
            "SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as success_count, "
            "SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) as error_count "
            "FROM agent_traces"
        ).fetchone()
        result = dict(row) if row else {}
        if result.get("total_runs", 0) > 0:
            result["success_rate"] = round(result.get("success_count", 0) / result["total_runs"] * 100, 2)
        else:
            result["success_rate"] = 0.0
        return result
