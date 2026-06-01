import json
from datetime import datetime
from typing import Optional
from uuid import uuid4

from cloud.app.repositories import NmpaComplianceLogsRepository
from cloud.app.services.base import BaseService

KEYWORDS = ["首个", "最佳", "最好", "第一", "绝对"]


def _log_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "log_id": row["log_id"],
        "document_type": row["document_type"],
        "content_summary": row["content_summary"],
        "check_result": row["check_result"],
        "violations_found": row["violations_found"],
        "violation_details": row["violation_details"],
        "human_review_required": row["human_review_required"],
        "human_reviewer": row["human_reviewer"],
        "human_reviewed_at": row["human_reviewed_at"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
    }


class NmpaService(BaseService):
    def check(self, document_type: str, content: str, user_id: int) -> dict:
        found = [kw for kw in KEYWORDS if kw in content]
        violations_found = len(found)
        check_result = "fail" if violations_found > 0 else "pass"
        human_review_required = 1 if violations_found > 0 else 0
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        content_summary = content[:200]
        log_id = f"nmpa:{uuid4()}"
        repo = NmpaComplianceLogsRepository(self.db)
        row_id = repo.create(
            {
                "log_id": log_id,
                "document_type": document_type,
                "content_summary": content_summary,
                "check_result": check_result,
                "violations_found": violations_found,
                "violation_details": json.dumps(found, ensure_ascii=False),
                "human_review_required": human_review_required,
                "created_by": user_id,
                "created_at": now,
            }
        )
        row = repo.get_by_id(row_id)
        return _log_to_dict(row)

    def list_logs(
        self,
        document_type: Optional[str] = None,
        check_result: Optional[str] = None,
        human_review_required: Optional[int] = None,
    ) -> list:
        repo = NmpaComplianceLogsRepository(self.db)
        rows = repo.list_filtered(
            document_type=document_type,
            check_result=check_result,
            human_review_required=human_review_required,
        )
        return [_log_to_dict(r) for r in rows]
