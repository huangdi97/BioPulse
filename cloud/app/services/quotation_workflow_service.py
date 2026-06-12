"""报价工作流服务，负责科研报价的提交、审批与驳回流程。"""

import json
from datetime import datetime, timezone

from cloud.app.research_database import get_research_db


def submit_for_approval(quotation_id: int, submitter: str):
    """提交报价单以供审批，将状态从草稿更新为待审批并记录审计日志。

    参数:
        quotation_id: 报价单 ID。
        submitter: 提交者标识。

    返回:
        None

    异常:
        ValueError: 报价单不存在或状态不是 draft。
    """
    db = get_research_db()
    try:
        row = db.execute("SELECT * FROM research_quotations WHERE quotation_id = ?", (quotation_id,)).fetchone()
        if not row:
            raise ValueError("Quotation not found")
        quotation = dict(row)
        if quotation["status"] != "draft":
            raise ValueError(f"Cannot submit quotation in status: {quotation['status']}")
        db.execute(
            "UPDATE research_quotations SET status = ? WHERE quotation_id = ?",
            ("pending_approval", quotation_id),
        )
        db.execute(
            "INSERT INTO research_audit_log (event_type, entity_type, entity_id, old_value, new_value, operator, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "submit_for_approval",
                "research_quotation",
                quotation_id,
                "draft",
                "pending_approval",
                submitter,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        db.commit()
    finally:
        db.close()


def approve(quotation_id: int, reviewer: str):
    """审批报价单，将状态从待审批更新为已批准并记录审计日志。

    参数:
        quotation_id: 报价单 ID。
        reviewer: 审批者标识。

    返回:
        None

    异常:
        ValueError: 报价单不存在或状态不是 pending_approval。
    """
    db = get_research_db()
    try:
        row = db.execute("SELECT * FROM research_quotations WHERE quotation_id = ?", (quotation_id,)).fetchone()
        if not row:
            raise ValueError("Quotation not found")
        quotation = dict(row)
        if quotation["status"] != "pending_approval":
            raise ValueError(f"Cannot approve quotation in status: {quotation['status']}")
        db.execute(
            "UPDATE research_quotations SET status = ? WHERE quotation_id = ?",
            ("approved", quotation_id),
        )
        db.execute(
            "INSERT INTO research_audit_log (event_type, entity_type, entity_id, old_value, new_value, operator, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "approve",
                "research_quotation",
                quotation_id,
                "pending_approval",
                "approved",
                reviewer,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        db.commit()
    finally:
        db.close()


def reject(quotation_id: int, reviewer: str, reason: str):
    """驳回报价单，将状态从待审批更新为已驳回，附带原因并记录审计日志。

    参数:
        quotation_id: 报价单 ID。
        reviewer: 审批者标识。
        reason: 驳回原因。

    返回:
        None

    异常:
        ValueError: 报价单不存在或状态不是 pending_approval。
    """
    db = get_research_db()
    try:
        row = db.execute("SELECT * FROM research_quotations WHERE quotation_id = ?", (quotation_id,)).fetchone()
        if not row:
            raise ValueError("Quotation not found")
        quotation = dict(row)
        if quotation["status"] != "pending_approval":
            raise ValueError(f"Cannot reject quotation in status: {quotation['status']}")
        old_status = quotation["status"]
        db.execute(
            "UPDATE research_quotations SET status = ? WHERE quotation_id = ?",
            ("rejected", quotation_id),
        )
        db.execute(
            "INSERT INTO research_audit_log (event_type, entity_type, entity_id, old_value, new_value, operator, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "reject",
                "research_quotation",
                quotation_id,
                old_status,
                json.dumps({"status": "rejected", "reason": reason}),
                reviewer,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        db.commit()
    finally:
        db.close()
