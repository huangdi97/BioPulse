import uuid
from datetime import datetime
from typing import Any, Optional

from shared.base_service import BaseService


class ApprovalService(BaseService):
    """审批服务 — 处理报价审批流程，包括合规校验与审批状态管理。"""

    def submit_quotation(self, quotation_data: dict) -> dict[str, Any]:
        product = quotation_data.get("product", "")
        amount = quotation_data.get("amount", 0)
        limit_amount = quotation_data.get("limit_amount")
        rep_id = quotation_data.get("rep_id", 0)

        compliance_passed = limit_amount is not None and amount <= limit_amount
        quotation_id = f"q-{uuid.uuid4().hex[:12]}"

        if compliance_passed:
            status = "auto_approved"
            message = "报价未超限，自动放行"
        else:
            status = "pending_approval"
            message = "报价超限，需人工审批"

        self.db.execute(
            "INSERT INTO quotation_approvals (quotation_id, rep_id, product, amount, limit_amount, status, compliance_passed) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (quotation_id, rep_id, product, amount, limit_amount, status, 1 if compliance_passed else 0),
        )
        self.db.commit()

        return {
            "quotation_id": quotation_id,
            "status": status,
            "message": message,
        }

    def get_pending(self) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT * FROM quotation_approvals WHERE status = 'pending_approval' ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def review(self, quotation_id: str, action: str, notes: str = "", reviewer: int = 1) -> Optional[dict[str, Any]]:
        row = self.db.execute("SELECT * FROM quotation_approvals WHERE quotation_id = ?", (quotation_id,)).fetchone()
        if not row:
            return None

        if action == "approve":
            new_status = "approved"
        elif action == "reject":
            new_status = "rejected"
        else:
            return None

        self.db.execute(
            "UPDATE quotation_approvals SET status = ?, review_notes = ?, reviewed_by = ?, reviewed_at = ? WHERE quotation_id = ?",
            (new_status, notes, reviewer, datetime.now().isoformat(), quotation_id),
        )
        self.db.commit()
        return {"quotation_id": quotation_id, "status": new_status}
