"""报价工作流服务，负责科研报价的提交、审批与驳回流程。"""

import json
from datetime import datetime, timezone

from cloud.app.research_database import get_research_db


def submit_for_approval(quotation_id: int, submitter: str):
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
