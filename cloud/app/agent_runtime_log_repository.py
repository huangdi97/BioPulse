"""AgentRuntimeLogRepository & AgentApprovalRepository."""

import json
import sqlite3
from datetime import datetime


class AgentRuntimeLogRepository:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def get_logs(self, agent_key: str | None = None, status: str | None = None, page: int = 1, page_size: int = 20) -> dict:
        conditions = []
        params = []
        if agent_key:
            conditions.append("agent_key = ?")
            params.append(agent_key)
        if status:
            conditions.append("status = ?")
            params.append(status)
        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        offset = (page - 1) * page_size
        total = self.db.execute(f"SELECT COUNT(*) as cnt FROM agent_runtime_logs{where}", params).fetchone()["cnt"]
        rows = self.db.execute(
            f"SELECT * FROM agent_runtime_logs{where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [page_size, offset],
        ).fetchall()
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [dict(r) for r in rows],
        }

    def create_log(
        self,
        agent_key: str,
        goal: str,
        status: str = "pending",
        iterations: int = 0,
        tool_calls: int = 0,
        log_detail: str = "[]",
        started_at: str | None = None,
        completed_at: str | None = None,
        trace_id: str = "",
        cost_data: str = "{}",
        result: str | None = None,
        error_message: str | None = None,
        checkpoint_data: str | None = None,
    ) -> int:
        cur = self.db.execute(
            "INSERT INTO agent_runtime_logs "
            "(agent_key, goal, status, iterations, tool_calls, log_detail, "
            "started_at, completed_at, trace_id, cost_data, result, error_message, checkpoint_data) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                agent_key,
                goal,
                status,
                iterations,
                tool_calls,
                log_detail,
                started_at,
                completed_at,
                trace_id,
                cost_data,
                result,
                error_message,
                checkpoint_data,
            ),
        )
        self.db.commit()
        return cur.lastrowid

    def update_status(
        self, log_id: int, status: str, result: str | None = None, error_message: str | None = None, completed_at: str | None = None
    ) -> bool:
        sets = ["status = ?"]
        params: list = [status]
        if result is not None:
            sets.append("result = ?")
            params.append(result)
        if error_message is not None:
            sets.append("error_message = ?")
            params.append(error_message)
        if completed_at is not None:
            sets.append("completed_at = ?")
            params.append(completed_at)
        params.append(log_id)
        cur = self.db.execute(f"UPDATE agent_runtime_logs SET {', '.join(sets)} WHERE id = ?", params)
        self.db.commit()
        return cur.rowcount > 0


class AgentApprovalRepository:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def get_approvals(self, status: str = "pending") -> list[dict]:
        rows = self.db.execute(
            "SELECT * FROM agent_runtime_approvals WHERE status = ? ORDER BY created_at ASC",
            (status,),
        ).fetchall()
        return [dict(r) for r in rows]

    def approve(self, approval_id: int, responded_by: str = "") -> bool:
        now = datetime.now().isoformat()
        cur = self.db.execute(
            "UPDATE agent_runtime_approvals SET status = 'approved', responded_at = ?, responded_by = ? WHERE id = ? AND status = 'pending'",
            (now, responded_by, approval_id),
        )
        self.db.commit()
        return cur.rowcount > 0

    def reject(self, approval_id: int, responded_by: str = "") -> bool:
        now = datetime.now().isoformat()
        cur = self.db.execute(
            "UPDATE agent_runtime_approvals SET status = 'rejected', responded_at = ?, responded_by = ? WHERE id = ? AND status = 'pending'",
            (now, responded_by, approval_id),
        )
        self.db.commit()
        return cur.rowcount > 0

    def update_approval_params(self, approval_id: int, params: dict) -> bool:
        now = datetime.now().isoformat()
        cur = self.db.execute(
            "UPDATE agent_runtime_approvals SET params = ?, responded_at = ? WHERE id = ? AND status = 'editing'",
            (json.dumps(params, ensure_ascii=False), now, approval_id),
        )
        self.db.commit()
        return cur.rowcount > 0
