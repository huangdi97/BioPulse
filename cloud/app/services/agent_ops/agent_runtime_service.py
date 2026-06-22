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
        """查询 Agent 运行日志，支持按 agent_key 和 status 筛选分页。"""
        conn = self._connect()
        try:
            repo = AgentRuntimeLogRepository(conn)
            return repo.get_logs(agent_key=agent_key, status=status, page=page, page_size=page_size)
        finally:
            conn.close()

    def get_status(self) -> dict:
        """获取 Agent 运行状态统计，按 status 分组计数。"""
        conn = self._connect()
        try:
            rows = conn.execute("SELECT status, COUNT(*) as count FROM agent_runtime_logs GROUP BY status").fetchall()
            return {r["status"]: r["count"] for r in rows}
        finally:
            conn.close()

    def list_pending_approvals(self) -> list[dict]:
        """列出所有待审批的 Agent 操作请求。"""
        conn = self._connect()
        try:
            repo = AgentApprovalRepository(conn)
            return repo.get_approvals(status="pending")
        finally:
            conn.close()

    def approve_approval(self, approval_id: int, username: str = "") -> bool:
        """审批通过一个待审批的 Agent 请求。"""
        conn = self._connect()
        try:
            repo = AgentApprovalRepository(conn)
            return repo.approve(approval_id, responded_by=username)
        finally:
            conn.close()

    def reject_approval(self, approval_id: int, username: str = "") -> bool:
        """驳回一个待审批的 Agent 请求。"""
        conn = self._connect()
        try:
            repo = AgentApprovalRepository(conn)
            return repo.reject(approval_id, responded_by=username)
        finally:
            conn.close()

    def execute_agent(self, goal: str, agent_key: str, context: dict | None, auth_header: str) -> dict:
        """执行指定 Agent 完成目标，返回执行结果。"""
        conn = self._connect()
        try:
            runtime = RuntimeCore(conn, conn, auth_header, agent_key)
            result = runtime.execute(goal, agent_key, context)
            return result.model_dump()
        finally:
            conn.close()

    def trigger_agent(self, agent_key: str, goal: str | None, auth_header: str) -> dict:
        """触发一个 Agent 按预配置目标或指定目标执行。"""
        spec = AGENT_SPECS.get(agent_key)
        if spec is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail=f"unknown agent_key: {agent_key}")
        goal = goal or spec["role_desc"]
        conn = self._connect()
        try:
            runtime = RuntimeCore(conn, conn, auth_header, agent_key)
            result = runtime.execute(goal, agent_key)
            return result.model_dump()
        finally:
            conn.close()

    def resume_execution(self, auth_header: str) -> dict:
        """恢复上一个未完成的 Agent 执行任务。"""
        conn = self._connect()
        try:
            runtime = RuntimeCore(conn, conn, auth_header, "")
            result = runtime.resume("", "")
            return result.model_dump()
        finally:
            conn.close()

    def rollback_execution(self, trace_id: str, step: int, auth_header: str) -> dict:
        """回滚指定执行到指定步骤的历史状态。"""
        conn = self._connect()
        try:
            runtime = RuntimeCore(conn, conn, auth_header, "")
            return runtime.rollback(trace_id, step)
        finally:
            conn.close()
