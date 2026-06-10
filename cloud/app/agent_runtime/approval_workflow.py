"""Agent 关键决策的人肉审批工作流。"""

import logging
from datetime import datetime, timedelta

from cloud.app.agent_runtime.approval_models import ApprovalRequestManager

logger = logging.getLogger(__name__)

APPROVAL_TIMEOUT_HOURS = 24
ESCALATION_INTERVAL_HOURS = [2, 8, 24]


class ApprovalWorkflow:
    """Agent 关键决策的人肉审批工作流。"""

    APPROVAL_REQUIRED_EVENTS = [
        "compliance.red_light.triggered",
        "compliance.rule.bypass",
        "cost.exceed_threshold",
        "agent.config_change",
    ]

    def __init__(self, db):
        self._manager = ApprovalRequestManager(db)
        self._db = db

    def request_approval(self, event_type: str, agent_name: str, detail: dict, timeout_hours: int = 24) -> str:
        request = self._manager.create_request(agent_name, event_type, detail)
        expires_at = datetime.now() + timedelta(hours=timeout_hours)
        self._db.execute(
            "UPDATE agent_runtime_approvals SET responded_at=? WHERE trace_id=?",
            (expires_at.isoformat(), request.request_id),
        )
        self._db.commit()
        logger.info("Approval requested: event=%s agent=%s request_id=%s", event_type, agent_name, request.request_id)
        return request.request_id

    def approve(self, request_id: str, approver: str):
        success = self._manager.approve(request_id, approver)
        if success:
            logger.info("Approval approved: request_id=%s approver=%s", request_id, approver)
        return success

    def reject(self, request_id: str, approver: str, reason: str):
        success = self._manager.reject(request_id, approver)
        if success:
            self._db.execute(
                "UPDATE agent_runtime_approvals SET reasoning=? WHERE trace_id=? AND status='rejected'",
                (reason, request_id),
            )
            self._db.commit()
            logger.info("Approval rejected: request_id=%s approver=%s reason=%s", request_id, approver, reason)
        return success

    def check_status(self, request_id: str) -> str:
        request = self._manager.get_request(request_id)
        if not request:
            return "not_found"
        if request.status == "pending" and request.created_at:
            created = datetime.fromisoformat(request.created_at)
            elapsed_hours = (datetime.now() - created).total_seconds() / 3600
            if elapsed_hours >= APPROVAL_TIMEOUT_HOURS:
                self._manager.reject(request_id, "system")
                return "timed_out"
        return request.status

    def get_pending_requests(self) -> list[dict]:
        return [r.to_dict() for r in self._manager.get_pending_requests()]

    def check_timeouts(self):
        return self._manager.check_timeouts()
