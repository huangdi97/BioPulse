"""Agent 运行时服务，管理 Agent 运行日志和审批流程。"""

import sqlite3

from cloud.app.agent_runtime.agent_specs import AGENT_SPECS
from cloud.app.agent_runtime.runtime_core import RuntimeCore
from cloud.app.agent_runtime_log_repository import (
    AgentApprovalRepository,
    AgentRuntimeLogRepository,
)
from cloud.app.database import DB_PATH


class AgentRuntimeService:
    """提供 Agent 运行时日志查询、状态统计与审批管理功能。"""

    def _connect(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def get_logs(self, agent_key: str | None = None, status: str | None = None, page: int = 1, page_size: int = 20) -> dict:
        conn = self._connect()
        try:
            repo = AgentRuntimeLogRepository(conn)
            return repo.get_logs(agent_key=agent_key, status=status, page=page, page_size=page_size)
        finally:
            conn.close()

    def get_status(self) -> dict:
        conn = self._connect()
        try:
            rows = conn.execute("SELECT status, COUNT(*) as count FROM agent_runtime_logs GROUP BY status").fetchall()
            return {r["status"]: r["count"] for r in rows}
        finally:
            conn.close()

    def list_pending_approvals(self) -> list[dict]:
        conn = self._connect()
        try:
            repo = AgentApprovalRepository(conn)
            return repo.get_approvals(status="pending")
        finally:
            conn.close()

    def approve_approval(self, approval_id: int, username: str = "") -> bool:
        conn = self._connect()
        try:
            repo = AgentApprovalRepository(conn)
            return repo.approve(approval_id, responded_by=username)
        finally:
            conn.close()

    def reject_approval(self, approval_id: int, username: str = "") -> bool:
        conn = self._connect()
        try:
            repo = AgentApprovalRepository(conn)
            return repo.reject(approval_id, responded_by=username)
        finally:
            conn.close()

    def execute_agent(self, goal: str, agent_key: str, context: dict | None, auth_header: str) -> dict:
        conn = self._connect()
        try:
            runtime = RuntimeCore(conn, conn, auth_header)
            result = runtime.execute(goal, agent_key, context)
            return result.model_dump()
        finally:
            conn.close()

    def trigger_agent(self, agent_key: str, goal: str | None, auth_header: str) -> dict:
        spec = AGENT_SPECS.get(agent_key)
        if spec is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail=f"unknown agent_key: {agent_key}")
        goal = goal or spec["role_desc"]
        conn = self._connect()
        try:
            runtime = RuntimeCore(conn, conn, auth_header)
            result = runtime.execute(goal, agent_key)
            return result.model_dump()
        finally:
            conn.close()

    def resume_execution(self, auth_header: str) -> dict:
        conn = self._connect()
        try:
            runtime = RuntimeCore(conn, conn, auth_header)
            result = runtime.resume("", "")
            return result.model_dump()
        finally:
            conn.close()

    def rollback_execution(self, trace_id: str, step: int, auth_header: str) -> dict:
        conn = self._connect()
        try:
            runtime = RuntimeCore(conn, conn, auth_header)
            return runtime.rollback(trace_id, step)
        finally:
            conn.close()
