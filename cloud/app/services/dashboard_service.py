from cloud.app.repositories import (
    AuditLogsRepository,
    ContentsRepository,
    UsersRepository,
)
from cloud.app.services.base import BaseService


class DashboardService(BaseService):
    def get_overview(self) -> dict:
        users_repo = UsersRepository(self.db)
        contents_repo = ContentsRepository(self.db)
        audit_repo = AuditLogsRepository(self.db)

        user_count = users_repo.count(conditions=["is_active=1"])
        content_count = contents_repo.count(conditions=["status!='archived'"])
        total_checks = contents_repo.count(conditions=["compliance_score IS NOT NULL"])
        passed_checks = contents_repo.count(conditions=["compliance_score IS NOT NULL", "compliance_score >= 1.0"])
        compliance_rate = round(passed_checks / total_checks * 100, 1) if total_checks > 0 else 0.0

        recent_logs = audit_repo.list_all(order_by="created_at DESC")[:10]
        recent_activity = [{k: r[k] for k in ("action", "entity_type", "entity_id", "created_at")} for r in recent_logs]

        return {
            "user_count": user_count,
            "content_count": content_count,
            "compliance_rate": compliance_rate,
            "recent_activity": recent_activity,
        }

    def get_user_stats(self) -> dict:
        db = self.db
        UsersRepository(db)
        by_role = db.execute("SELECT role, COUNT(*) as cnt FROM users WHERE is_active=1 GROUP BY role").fetchall()
        trend = db.execute(
            "SELECT DATE(created_at) as day, COUNT(*) as cnt FROM users "
            "WHERE created_at IS NOT NULL GROUP BY DATE(created_at) ORDER BY day DESC LIMIT 30"
        ).fetchall()

        return {
            "by_role": [dict(r) for r in by_role],
            "registration_trend": [dict(r) for r in reversed(trend)],
        }

    def get_compliance_stats(self) -> dict:
        db = self.db
        contents_repo = ContentsRepository(db)
        total = contents_repo.count(conditions=["compliance_score IS NOT NULL"])
        passed = contents_repo.count(conditions=["compliance_score IS NOT NULL", "compliance_score >= 1.0"])
        failed = total - passed
        pass_rate = round(passed / total * 100, 1) if total > 0 else 0.0

        by_category = db.execute(
            "SELECT category, COUNT(*) as cnt FROM contents WHERE compliance_score IS NOT NULL AND compliance_score < 1.0 "
            "GROUP BY category ORDER BY cnt DESC"
        ).fetchall()

        trend = db.execute(
            "SELECT DATE(created_at) as day, "
            "COUNT(*) as total, "
            "SUM(CASE WHEN compliance_score >= 1.0 THEN 1 ELSE 0 END) as passed "
            "FROM contents WHERE compliance_score IS NOT NULL "
            "GROUP BY DATE(created_at) ORDER BY day DESC LIMIT 30"
        ).fetchall()

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": pass_rate,
            "by_category": [dict(r) for r in by_category],
            "trend": [dict(r) for r in reversed(trend)],
        }

    def get_content_stats(self) -> dict:
        db = self.db
        ContentsRepository(db)
        by_category = db.execute("SELECT category, COUNT(*) as cnt FROM contents WHERE status!='archived' GROUP BY category").fetchall()
        by_status = db.execute("SELECT status, COUNT(*) as cnt FROM contents WHERE status!='archived' GROUP BY status").fetchall()
        daily_trend = db.execute(
            "SELECT DATE(created_at) as day, COUNT(*) as cnt FROM contents GROUP BY DATE(created_at) ORDER BY day DESC LIMIT 30"
        ).fetchall()

        return {
            "by_category": [dict(r) for r in by_category],
            "by_status": [dict(r) for r in by_status],
            "daily_trend": [dict(r) for r in reversed(daily_trend)],
        }
