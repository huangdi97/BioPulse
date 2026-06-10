"""Agent 运行时存储抽象层。"""

import json
from abc import ABC, abstractmethod


class AgentStorage(ABC):
    """Agent 运行时存储抽象层。"""

    @abstractmethod
    def save_trace(self, trace: dict): ...

    @abstractmethod
    def query_traces(self, agent_name: str = None, limit: int = 20, offset: int = 0) -> list[dict]: ...

    @abstractmethod
    def save_eval_result(self, result: dict): ...

    @abstractmethod
    def save_cost_record(self, record: dict): ...

    @abstractmethod
    def get_prompt_version(self, agent_name: str, version_id: int = None) -> dict | None: ...


class SQLiteAgentStorage(AgentStorage):
    """SQLite 实现（当前）。"""

    def __init__(self, db):
        self._db = db

    def save_trace(self, trace: dict):
        self._db.execute(
            "INSERT INTO agent_traces "
            "(trace_id, agent_name, user_id, input_data, output_data, status, "
            "total_duration_ms, total_prompt_tokens, total_completion_tokens, "
            "tool_calls_json, llm_calls_json, started_at, ended_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                trace.get("trace_id", ""),
                trace.get("agent_name", ""),
                trace.get("user_id", ""),
                json.dumps(trace.get("input_data", {}), ensure_ascii=False),
                json.dumps(trace.get("output_data", {}), ensure_ascii=False),
                trace.get("status", ""),
                trace.get("total_duration_ms", 0),
                trace.get("total_prompt_tokens", 0),
                trace.get("total_completion_tokens", 0),
                json.dumps(trace.get("tool_calls", []), ensure_ascii=False),
                json.dumps(trace.get("llm_calls", []), ensure_ascii=False),
                trace.get("started_at", ""),
                trace.get("ended_at", ""),
            ),
        )
        self._db.commit()

    def query_traces(self, agent_name: str = None, limit: int = 20, offset: int = 0) -> list[dict]:
        conditions = []
        params = []
        if agent_name:
            conditions.append("agent_name = ?")
            params.append(agent_name)
        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = self._db.execute(
            f"SELECT * FROM agent_traces{where} ORDER BY started_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return [dict(r) for r in rows]

    def save_eval_result(self, result: dict):
        self._db.execute(
            "INSERT INTO agent_eval_results (agent_name, trace_id, input_data, output_data, expected_data, metrics_json, passed, score) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                result.get("agent_name", ""),
                result.get("trace_id", ""),
                json.dumps(result.get("input_data", {}), ensure_ascii=False),
                json.dumps(result.get("output_data", {}), ensure_ascii=False),
                json.dumps(result.get("expected", {}), ensure_ascii=False),
                json.dumps(result.get("metrics", {}), ensure_ascii=False),
                1 if result.get("passed") else 0,
                result.get("score", 0.0),
            ),
        )
        self._db.commit()

    def save_cost_record(self, record: dict):
        self._db.execute(
            "INSERT INTO agent_cost_tracking (agent_name, trace_id, model, model_tier, input_tokens, output_tokens, cost, step, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                record.get("agent_name", ""),
                record.get("trace_id", ""),
                record.get("model", ""),
                record.get("model_tier", ""),
                record.get("input_tokens", 0),
                record.get("output_tokens", 0),
                record.get("cost", 0.0),
                record.get("step", 0),
                record.get("created_at", ""),
            ),
        )
        self._db.commit()

    def get_prompt_version(self, agent_name: str, version_id: int = None) -> dict | None:
        if version_id:
            row = self._db.execute(
                "SELECT * FROM prompt_versions WHERE agent_name=? AND version_id=? AND status='approved'",
                (agent_name, version_id),
            ).fetchone()
        else:
            row = self._db.execute(
                "SELECT * FROM prompt_versions WHERE agent_name=? AND status='approved' ORDER BY version_id DESC LIMIT 1",
                (agent_name,),
            ).fetchone()
        return dict(row) if row else None
