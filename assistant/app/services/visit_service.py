"""拜访管理服务模块。"""

from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from starlette import status

from assistant.app.repositories import HcpRepository, VisitRecordRepository
from assistant.app.services.base import BaseService


class VisitService(BaseService):
    """拜访管理服务，提供拜访记录的增删改查与智能评分。"""

    def _check_hcp_exists(self, conn, hcp_id: int) -> None:
        repo = HcpRepository(conn)
        row = repo.get_by_id(hcp_id)
        if not row or row["is_active"] != 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HCP not found")

    def create_visit(self, body, user_id: int) -> dict:
        conn = self._connection()
        try:
            self._check_hcp_exists(conn, body.hcp_id)
            repo = VisitRecordRepository(conn)
            row_id = repo.create(
                body.model_dump(),
                extra={"created_by": user_id},
            )
            return {"id": row_id}
        finally:
            conn.close()

    def list_visits(
        self,
        page: int,
        page_size: int,
        hcp_id: Optional[int] = None,
        visit_type: Optional[str] = None,
    ) -> tuple:
        conn = self._connection()
        try:
            repo = VisitRecordRepository(conn)
            conditions: List[str] = []
            params: list = []

            if hcp_id is not None:
                conditions.append("hcp_id = ?")
                params.append(hcp_id)
            if visit_type:
                conditions.append("visit_type = ?")
                params.append(visit_type)

            return repo.paginate(
                page=page,
                page_size=page_size,
                conditions=conditions,
                params=params,
            )
        finally:
            conn.close()

    def get_visit(self, visit_id: int) -> dict:
        conn = self._connection()
        try:
            repo = VisitRecordRepository(conn)
            row = repo.get_by_id(visit_id)
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
            return dict(row)
        finally:
            conn.close()

    def update_visit(self, visit_id: int, body) -> dict:
        conn = self._connection()
        try:
            repo = VisitRecordRepository(conn)
            row = repo.get_by_id(visit_id)
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")

            if body.hcp_id is not None:
                self._check_hcp_exists(conn, body.hcp_id)

            updates = body.model_dump(exclude_unset=True)
            if not updates:
                return dict(row)

            repo.update(visit_id, updates)
            return dict(repo.get_by_id(visit_id))
        finally:
            conn.close()

    def delete_visit(self, visit_id: int) -> None:
        conn = self._connection()
        try:
            repo = VisitRecordRepository(conn)
            row = repo.get_by_id(visit_id)
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
            repo.soft_delete(visit_id)
        finally:
            conn.close()

    def _offline_visit_score(self, visit_data: dict) -> dict:
        base_score = 50

        scheduled_date = visit_data.get("scheduled_date")
        if scheduled_date:
            days_until = (datetime.strptime(scheduled_date, "%Y-%m-%d") - datetime.now()).days
            urgency_score = max(0, min(20, (30 - days_until) / 30 * 20))
        else:
            urgency_score = 5

        hcp_value = 15 if visit_data.get("hcp_value") == "high" else (8 if visit_data.get("hcp_value") == "medium" else 0)

        history_score = 10 if visit_data.get("previous_visits", 0) > 0 else 0

        conflict_penalty = -10 if visit_data.get("has_conflict") else 0

        total = base_score + urgency_score + hcp_value + history_score + conflict_penalty

        return {
            "score": max(0, min(100, total)),
            "level": "high" if total >= 70 else ("medium" if total >= 40 else "low"),
            "urgency": "urgent" if urgency_score >= 15 else "normal",
            "source": "offline_rule",
            "breakdown": {
                "base": base_score,
                "urgency": round(urgency_score, 1),
                "hcp_value": hcp_value,
                "history": history_score,
                "conflict_penalty": conflict_penalty,
            },
        }

    def get_visit_score(self, visit_id: int, offline_mode: bool = False) -> dict:
        visit_data = self.get_visit(visit_id)
        if offline_mode:
            return self._offline_visit_score(visit_data)
        return self._offline_visit_score(visit_data)
