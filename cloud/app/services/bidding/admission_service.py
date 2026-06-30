"""入院流程状态机服务。"""

import json
from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import HTTPException
from starlette import status

from shared.base_service import BaseService


class AdmissionStatus(str, Enum):
    FILING = "备案"
    DEPT_SUBMIT = "科室提交"
    PURCHASE_REVIEW = "采购处审核"
    PHARMACY_COMMITTEE = "药事会"
    BIDDING = "招标"
    ADMITTED = "入院"


_STEPS = list(AdmissionStatus)


class _AdmissionRecord:
    def __init__(self, row) -> None:
        self.id: int = row["id"]
        self.hcp_id: int = row["hcp_id"]
        self.product_id: int = row["product_id"]
        self.current_status: str = row["current_status"]
        self.steps: list[dict] = json.loads(row["steps"]) if row["steps"] else []
        self.created_at: str = row["created_at"]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "hcp_id": self.hcp_id,
            "product_id": self.product_id,
            "current_status": self.current_status,
            "steps": self.steps,
            "created_at": self.created_at,
        }


class AdmissionService(BaseService):
    def __init__(self, db=None):
        super().__init__(db)
        self._init_table()

    def _init_table(self) -> None:
        conn = self._connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admission_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hcp_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                current_status TEXT NOT NULL,
                steps TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()

    def create(self, hcp_id: int, product_id: int) -> dict:
        conn = self._connection()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        first_status = _STEPS[0].value
        step = {"status": first_status, "timestamp": now, "approver": "system", "notes": "新建入院流程"}
        steps_json = json.dumps([step], ensure_ascii=False)
        cur = conn.execute(
            "INSERT INTO admission_records (hcp_id, product_id, current_status, steps, created_at) VALUES (?, ?, ?, ?, ?)",
            (hcp_id, product_id, first_status, steps_json, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM admission_records WHERE id = ?", (cur.lastrowid,)).fetchone()
        return _AdmissionRecord(row).to_dict()

    def advance_status(self, record_id: int, approver: str, notes: str = "") -> dict:
        conn = self._connection()
        row = conn.execute("SELECT * FROM admission_records WHERE id = ?", (record_id,)).fetchone()
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Admission record not found")
        record = _AdmissionRecord(row)
        current_idx = next((i for i, s in enumerate(_STEPS) if s.value == record.current_status), -1)
        if current_idx == -1 or current_idx >= len(_STEPS) - 1:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No next status available")
        next_status = _STEPS[current_idx + 1].value
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        step = {"status": next_status, "timestamp": now, "approver": approver, "notes": notes}
        record.current_status = next_status
        record.steps.append(step)
        steps_json = json.dumps(record.steps, ensure_ascii=False)
        conn.execute(
            "UPDATE admission_records SET current_status = ?, steps = ? WHERE id = ?",
            (next_status, steps_json, record_id),
        )
        conn.commit()
        return record.to_dict()

    def get_status(self, record_id: int) -> dict:
        conn = self._connection()
        row = conn.execute("SELECT * FROM admission_records WHERE id = ?", (record_id,)).fetchone()
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Admission record not found")
        return _AdmissionRecord(row).to_dict()

    def summary(self, hcp_id: Optional[int] = None, product_id: Optional[int] = None) -> list[dict]:
        conn = self._connection()
        query = "SELECT * FROM admission_records WHERE 1=1"
        params: list = []
        if hcp_id is not None:
            query += " AND hcp_id = ?"
            params.append(hcp_id)
        if product_id is not None:
            query += " AND product_id = ?"
            params.append(product_id)
        query += " ORDER BY created_at DESC"
        rows = conn.execute(query, params).fetchall()
        return [_AdmissionRecord(r).to_dict() for r in rows]
