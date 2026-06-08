"""合规 V2 报告模块，提供审计复核、审计链查验、纠偏训练与仪表盘。"""

import hashlib
import json
import math
from typing import Optional

from fastapi import Request

from cloud.app.repositories import (
    AuditChainEntriesRepository,
    ComplianceAuditRecordsRepository,
    TrainingCorrectionsRepository,
)
from cloud.app.services.base import BaseService
from cloud.app.services.report_templates import (
    TRAINING_SYS_PROMPT,
    _call_ai,
    _n404,
    _now,
    _parse_json,
    build_dashboard_data,
)
from shared.base import PaginatedResponse, success


class ReportGenerator(BaseService):
    """报告生成器，提供记录复核、哈希链审计、AI 纠偏训练及统计仪表盘。"""

    def review_record(self, record_id: int, body, uid: int) -> dict:
        audit_repo = ComplianceAuditRecordsRepository(self.db)
        chain_repo = AuditChainEntriesRepository(self.db)
        row = audit_repo.get_by_id(record_id)
        if not row:
            _n404("Record")
        n = _now()
        audit_repo.update(record_id, {"reviewed_by": uid, "reviewed_at": n})
        chain_repo.create(
            {
                "entity_type": "compliance_audit",
                "entity_id": str(record_id),
                "action": "review",
                "previous_hash": "",
                "current_hash": hashlib.sha256(
                    json.dumps(
                        {
                            "action": "review",
                            "record_id": record_id,
                            "notes": body.review_notes,
                        }
                    ).encode()
                ).hexdigest(),
                "payload": json.dumps(
                    {
                        "override_passed": body.override_passed,
                        "review_notes": body.review_notes,
                    },
                    ensure_ascii=False,
                ),
                "source": "",
                "created_by": uid,
                "performed_at": n,
            }
        )
        return success(data=audit_repo.get_by_id(record_id))

    def create_audit_chain(self, body, uid: int) -> dict:
        repo = AuditChainEntriesRepository(self.db)
        n = _now()
        prev_hash = ""
        latest_rows = repo.list_all(
            conditions=["entity_type=?", "entity_id=?"],
            params=[body.entity_type, body.entity_id],
            order_by="performed_at DESC",
        )
        if latest_rows:
            prev_hash = latest_rows[0]["current_hash"]
        current_hash = hashlib.sha256((prev_hash + json.dumps(body.payload, ensure_ascii=False, sort_keys=True)).encode("utf-8")).hexdigest()
        repo.create(
            {
                "entity_type": body.entity_type,
                "entity_id": body.entity_id,
                "action": body.action,
                "previous_hash": prev_hash,
                "current_hash": current_hash,
                "payload": json.dumps(body.payload, ensure_ascii=False),
                "metadata": json.dumps(body.metadata, ensure_ascii=False),
                "source": body.source,
                "created_by": uid,
                "performed_at": n,
            }
        )
        return success(
            data={
                "entity_type": body.entity_type,
                "entity_id": body.entity_id,
                "current_hash": current_hash,
                "previous_hash": prev_hash,
            }
        )

    def get_audit_chain(self, entity_type: str, entity_id: str) -> dict:
        repo = AuditChainEntriesRepository(self.db)
        rows = repo.list_all(
            conditions=["entity_type=?", "entity_id=?"],
            params=[entity_type, entity_id],
            order_by="performed_at ASC",
        )
        return success(data=rows)

    def verify_audit_chain(self, entity_type: str, entity_id: str) -> dict:
        repo = AuditChainEntriesRepository(self.db)
        rows = repo.list_all(
            conditions=["entity_type=?", "entity_id=?"],
            params=[entity_type, entity_id],
            order_by="performed_at ASC",
        )
        valid = True
        broken_at = None
        for i, row in enumerate(rows):
            expected_prev = rows[i - 1]["current_hash"] if i > 0 else ""
            if row["previous_hash"] != expected_prev:
                valid = False
                broken_at = row["id"]
                break
            payload = _parse_json(row["payload"], {}) if isinstance(row["payload"], str) else row["payload"]
            recomputed = hashlib.sha256((row["previous_hash"] + json.dumps(payload, ensure_ascii=False, sort_keys=True)).encode("utf-8")).hexdigest()
            if recomputed != row["current_hash"]:
                valid = False
                broken_at = row["id"]
                break
        return success(
            data={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "valid": valid,
                "total_entries": len(rows),
                "broken_at": broken_at,
            }
        )

    def train_correction(self, record_id: int, request: Request, uid: int) -> dict:
        audit_repo = ComplianceAuditRecordsRepository(self.db)
        corrections_repo = TrainingCorrectionsRepository(self.db)
        row = audit_repo.get_by_id(record_id)
        if not row:
            _n404("Record")
        violations = _parse_json(row["violations"], [])
        messages = [
            {"role": "system", "content": TRAINING_SYS_PROMPT},
            {
                "role": "user",
                "content": f"内容类型: {row['message_type']}\n内容: {row['content']}\n违规: {json.dumps(violations, ensure_ascii=False)}\n风险等级: {row['risk_level']}",
            },
        ]
        auth = request.headers.get("Authorization", "")
        ai_data = _call_ai(messages, auth)
        ai_reply = ai_data.get("reply", "")
        parsed = _parse_json(ai_reply, {})
        if isinstance(parsed, dict):
            title = parsed.get("title", "培训纠正")
            desc = parsed.get("description", ai_reply[:300])
            cat = parsed.get("category", "general")
            sev = parsed.get("severity", "medium")
        else:
            title = "培训纠正"
            desc = ai_reply[:300]
            cat = "general"
            sev = "medium"
        n = _now()
        corrections_repo.create(
            {
                "audit_record_id": record_id,
                "title": title,
                "description": desc,
                "category": cat,
                "severity": sev,
                "status": "pending",
                "created_by": uid,
                "created_at": n,
            }
        )
        return success(
            data={
                "audit_record_id": record_id,
                "title": title,
                "description": desc,
                "category": cat,
                "severity": sev,
            }
        )

    def list_corrections(
        self,
        category: Optional[str],
        severity: Optional[str],
        status: Optional[str],
        page: int,
        page_size: int,
    ) -> dict:
        repo = TrainingCorrectionsRepository(self.db)
        conditions, params = [], []
        if category:
            conditions.append("category=?")
            params.append(category)
        if severity:
            conditions.append("severity=?")
            params.append(severity)
        if status:
            conditions.append("status=?")
            params.append(status)
        total, _, rows = repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )
        total_pages = math.ceil(total / max(page_size, 1))
        return success(
            data=PaginatedResponse(
                items=rows,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )
        )

    def update_correction(self, correction_id: int, body) -> dict:
        repo = TrainingCorrectionsRepository(self.db)
        row = repo.get_by_id(correction_id)
        if not row:
            _n404("Correction")
        updates = {}
        if body.status is not None:
            updates["status"] = body.status
        if body.assigned_to is not None:
            updates["assigned_to"] = body.assigned_to
        if updates:
            repo.update(correction_id, updates)
        return success(data=repo.get_by_id(correction_id))

    def dashboard(self) -> dict:
        audit_repo = ComplianceAuditRecordsRepository(self.db)
        corrections_repo = TrainingCorrectionsRepository(self.db)
        return success(data=build_dashboard_data(self.db, audit_repo, corrections_repo))
