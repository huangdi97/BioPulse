"""审计日志服务，负责审计日志的创建、查询与统计。"""

from datetime import datetime, timedelta
from typing import Optional

from cloud.app.repositories import AuditLogsRepository
from shared.base_service import BaseService


class AuditService(BaseService):
    """审计服务，记录操作日志并支持按条件检索与趋势统计。"""

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
        """创建一条审计日志记录。"""
        repo = AuditLogsRepository(self.db)
        repo.create(
            {
                "user_id": user_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "detail": detail,
                "source_end": source_end,
                "ip_address": ip_address,
            }
        )

    def list_logs(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """按条件分页查询审计日志。"""
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
            page=page,
            page_size=page_size,
            conditions=conds or None,
            params=pars or None,
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
        """获取审计日志统计，含按操作分组的计数和近 7 日趋势。"""
        repo = AuditLogsRepository(self.db)
        action_stats = repo.execute("SELECT action, COUNT(*) as cnt FROM audit_logs GROUP BY action").fetchall()
        cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        trend = repo.execute(
            "SELECT DATE(created_at) as day, COUNT(*) as cnt FROM audit_logs WHERE created_at >= ? GROUP BY day ORDER BY day",
            (cutoff,),
        ).fetchall()
        return {
            "by_action": [dict(r) for r in action_stats],
            "daily_trend": [dict(r) for r in trend],
        }
