from typing import Any, List, Optional
from datetime import datetime, timedelta

from cloud.app.repositories import AuditLogsRepository
from cloud.app.services.base import BaseService
from shared.base import PaginatedResponse


class AuditService(BaseService):
    def create_log(
        self,
        user_id: int,
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        detail: str = "",
        source_end: str = "cloud",
        ip_address: str = "",
    ) -> None:
        repo = AuditLogsRepository(self.db)
        repo.create({
            "user_id": user_id, "action": action,
            "entity_type": entity_type, "entity_id": entity_id,
            "detail": detail, "source_end": source_end,
            "ip_address": ip_address,
        })

    def list_logs(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        repo = AuditLogsRepository(self.db)
        conds, pars = [], []
        if entity_type:
            conds.append("entity_type=?")
            pars.append(entity_type)
        if entity_id is not None:
            conds.append("entity_id=?")
            pars.append(entity_id)
        if action:
            conds.append("action=?")
            pars.append(action)
        if user_id is not None:
            conds.append("user_id=?")
            pars.append(user_id)
        total, total_pages, rows = repo.paginate(
            page=page, page_size=page_size,
            conditions=conds or None, params=pars or None,
            order_by="created_at DESC",
        )
        return {
            "items": rows,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_stats(self) -> dict:
        db = self.db
        action_stats = db.execute(
            "SELECT action, COUNT(*) as cnt FROM audit_logs GROUP BY action"
        ).fetchall()
        cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        trend = db.execute(
            "SELECT DATE(created_at) as day, COUNT(*) as cnt "
            "FROM audit_logs WHERE created_at >= ? "
            "GROUP BY day ORDER BY day",
            (cutoff,)
        ).fetchall()
        return {
            "by_action": [dict(r) for r in action_stats],
            "daily_trend": [dict(r) for r in trend],
        }
