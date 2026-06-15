from datetime import datetime
from typing import Any, Optional

from shared.base_service import BaseService

STATUSES = ["待提交", "药事会排期", "审批中", "已通过", "已驳回"]


class AdmissionService(BaseService):
    """入院申请服务 — 管理药品入院申请的创建、审批流程与状态跟踪。"""

    def create(self, data: dict) -> dict[str, Any]:
        self.db.execute(
            "INSERT INTO admission_records (hospital_name, department, product, status, meeting_date, notes, rep_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                data["hospital_name"],
                data.get("department", ""),
                data["product"],
                data.get("status", "待提交"),
                data.get("meeting_date"),
                data.get("notes", ""),
                data.get("rep_id", 0),
            ),
        )
        self.db.commit()
        row_id = self.db.execute("SELECT last_insert_rowid()").fetchone()[0]
        return self.get_by_id(row_id)

    def get_by_id(self, record_id: int) -> Optional[dict[str, Any]]:
        row = self.db.execute("SELECT * FROM admission_records WHERE id = ?", (record_id,)).fetchone()
        if not row:
            return None
        return dict(row)

    def list(self, status: Optional[str] = None, rep_id: Optional[int] = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM admission_records WHERE 1=1"
        params = []
        if status:
            sql += " AND status = ?"
            params.append(status)
        if rep_id:
            sql += " AND rep_id = ?"
            params.append(rep_id)
        sql += " ORDER BY created_at DESC"
        rows = self.db.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def update_status(self, record_id: int, new_status: str) -> Optional[dict[str, Any]]:
        if new_status not in STATUSES:
            return None
        self.db.execute(
            "UPDATE admission_records SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, datetime.now().isoformat(), record_id),
        )
        self.db.commit()
        return self.get_by_id(record_id)
