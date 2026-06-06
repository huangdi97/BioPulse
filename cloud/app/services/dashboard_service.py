"""仪表盘服务，提供概览统计与合规分析数据。"""

from cloud.app.repositories import (
    AuditLogsRepository,
    ContentsRepository,
    UsersRepository,
)
from cloud.app.services.base import BaseService


class DashboardService(BaseService):
    """仪表盘服务，汇总用户、内容与合规统计数据。"""

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
        users_repo = UsersRepository(self.db)
        by_role = users_repo.execute("SELECT role, COUNT(*) as cnt FROM users WHERE is_active=1 GROUP BY role").fetchall()
        trend = users_repo.execute(
            "SELECT DATE(created_at) as day, COUNT(*) as cnt FROM users "
            "WHERE created_at IS NOT NULL GROUP BY DATE(created_at) ORDER BY day DESC LIMIT 30"
        ).fetchall()

        return {
            "by_role": [dict(r) for r in by_role],
            "registration_trend": [dict(r) for r in reversed(trend)],
        }

    def get_compliance_stats(self) -> dict:
        contents_repo = ContentsRepository(self.db)
        total = contents_repo.count(conditions=["compliance_score IS NOT NULL"])
        passed = contents_repo.count(conditions=["compliance_score IS NOT NULL", "compliance_score >= 1.0"])
        failed = total - passed
        pass_rate = round(passed / total * 100, 1) if total > 0 else 0.0

        by_category = contents_repo.execute(
            "SELECT category, COUNT(*) as cnt FROM contents WHERE compliance_score IS NOT NULL AND compliance_score < 1.0 "
            "GROUP BY category ORDER BY cnt DESC"
        ).fetchall()

        trend = contents_repo.execute(
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
        contents_repo = ContentsRepository(self.db)
        by_category = contents_repo.execute("SELECT category, COUNT(*) as cnt FROM contents WHERE status!='archived' GROUP BY category").fetchall()
        by_status = contents_repo.execute("SELECT status, COUNT(*) as cnt FROM contents WHERE status!='archived' GROUP BY status").fetchall()
        daily_trend = contents_repo.execute(
            "SELECT DATE(created_at) as day, COUNT(*) as cnt FROM contents GROUP BY DATE(created_at) ORDER BY day DESC LIMIT 30"
        ).fetchall()

        return {
            "by_category": [dict(r) for r in by_category],
            "by_status": [dict(r) for r in by_status],
            "daily_trend": [dict(r) for r in reversed(daily_trend)],
        }

    def get_visit_trends(self) -> list:
        rows = self.db.execute(
            "SELECT DATE(created_at) as date, COUNT(*) as count "
            "FROM visits "
            "WHERE created_at >= DATE('now', '-30 days') "
            "GROUP BY DATE(created_at) "
            "ORDER BY date ASC"
        ).fetchall()
        return [{"date": r["date"], "count": r["count"]} for r in rows]

    def get_team_ranks(self) -> list:
        rows = self.db.execute(
            "SELECT t.name as team_name, "
            "COUNT(DISTINCT ut.user_id) as score, "
            "COUNT(DISTINCT ut.user_id) as member_count "
            "FROM teams t "
            "LEFT JOIN user_team ut ON t.id = ut.team_id "
            "WHERE t.is_active = 1 "
            "GROUP BY t.id "
            "ORDER BY score DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_violations(self) -> list:
        rows = self.db.execute(
            "SELECT rule_id, rule_name, severity, visit_data_json as detail, created_at FROM compliance_l2_log ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_research_kpis(self) -> list:
        pi_count = self.db.execute("SELECT COUNT(*) as cnt FROM pi_profiles").fetchone()["cnt"]
        product_count = self.db.execute("SELECT COUNT(*) as cnt FROM products").fetchone()["cnt"]

        from cloud.app.research_database import get_research_db

        research_db = get_research_db()
        try:
            quotation_count = research_db.execute("SELECT COUNT(*) as cnt FROM research_quotations").fetchone()["cnt"]
        finally:
            research_db.close()

        return [
            {"kpi_name": "在研PI数", "value": pi_count},
            {"kpi_name": "产品总数", "value": product_count},
            {"kpi_name": "报价单数", "value": quotation_count},
        ]

    def get_pi_sources(self) -> list:
        try:
            self.db.execute("ALTER TABLE pi_profiles ADD COLUMN source TEXT NOT NULL DEFAULT ''")
        except Exception:
            pass  # 兼容操作：列已存在时跳过
        rows = self.db.execute(
            "SELECT COALESCE(NULLIF(source, ''), institution) as source, COUNT(*) as count FROM pi_profiles GROUP BY source ORDER BY count DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_product_match_stats(self) -> list:
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS product_matches ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "product_id INTEGER, "
            "pi_id INTEGER, "
            "match_score REAL, "
            "category TEXT, "
            "created_at TEXT DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        rows = self.db.execute(
            "SELECT category, COUNT(*) as total, AVG(match_score) as avg_score FROM product_matches GROUP BY category ORDER BY total DESC"
        ).fetchall()
        return [dict(r) for r in rows]
