from fastapi import Depends

from cloud.app.agent_database import (
    AgentApprovalRepository,
    AgentRuntimeLogRepository,
    get_agent_db,
)


class AgentRuntimeService:
    def __init__(self, db=Depends(get_agent_db)):
        self.db = db

    def get_logs(self, agent_key: str | None = None, status: str | None = None, page: int = 1, page_size: int = 20) -> dict:
        repo = AgentRuntimeLogRepository(self.db)
        return repo.get_logs(agent_key=agent_key, status=status, page=page, page_size=page_size)

    def get_status(self) -> dict:
        rows = self.db.execute("SELECT status, COUNT(*) as count FROM agent_runtime_logs GROUP BY status").fetchall()
        return {r["status"]: r["count"] for r in rows}

    def list_pending_approvals(self) -> list[dict]:
        repo = AgentApprovalRepository(self.db)
        return repo.get_approvals(status="pending")

    def approve_approval(self, approval_id: int, username: str = "") -> bool:
        repo = AgentApprovalRepository(self.db)
        return repo.approve(approval_id, responded_by=username)

    def reject_approval(self, approval_id: int, username: str = "") -> bool:
        repo = AgentApprovalRepository(self.db)
        return repo.reject(approval_id, responded_by=username)
