"""仪表盘服务，提供概览统计与合规分析数据。"""

from cloud.app.repositories import (
    AuditLogsRepository,
    ContentsRepository,
    UsersRepository,
)
from shared.base_service import BaseService


class DashboardService(BaseService):
    """仪表盘服务，汇总用户、内容与合规统计数据。"""

    def get_overview(self) -> dict:
        """获取仪表盘概览统计，包含用户数、内容数、合规率及近期活动。

        返回:
            包含 user_count、content_count、compliance_rate 和 recent_activity 的字典。
        """
        users_repo = UsersRepository(self._connection())
        contents_repo = ContentsRepository(self._connection())
        audit_repo = AuditLogsRepository(self._connection())

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
        """获取用户统计数据，包含按角色分布和近 30 日注册趋势。

        返回:
            包含 by_role（角色分布）和 registration_trend（注册趋势）的字典。
        """
        users_repo = UsersRepository(self._connection())
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
        """获取合规统计数据，包含通过/失败数、通过率、按类别分布及趋势。

        返回:
            包含 total、passed、failed、pass_rate、by_category 和 trend 的字典。
        """
        contents_repo = ContentsRepository(self._connection())
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
        """获取内容统计数据，包含按类别、状态分布及每日创建趋势。

        返回:
            包含 by_category、by_status 和 daily_trend 的字典。
        """
        contents_repo = ContentsRepository(self._connection())
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
        """获取近 30 天访问量趋势数据。

        返回:
            包含日期和访问次数的字典列表。
        """
        rows = self.db.execute(
            "SELECT DATE(created_at) as date, COUNT(*) as count "
            "FROM visits "
            "WHERE created_at >= DATE('now', '-30 days') "
            "GROUP BY DATE(created_at) "
            "ORDER BY date ASC"
        ).fetchall()
        return [{"date": r["date"], "count": r["count"]} for r in rows]

    def get_team_ranks(self) -> list:
        """获取团队排名，按成员数降序排列。

        返回:
            包含 team_name、score 和 member_count 的字典列表。
        """
        conn = self._connection()
        conn.execute("CREATE TABLE IF NOT EXISTS teams (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, is_active INTEGER DEFAULT 1)")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS user_team (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, team_id INTEGER NOT NULL)"
        )
        rows = conn.execute(
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
        """获取最近 50 条合规违规记录。

        返回:
            包含规则、严重级别和详细信息的字典列表。
        """
        rows = self.db.execute(
            "SELECT rule_id, rule_name, severity, visit_data_json as detail, created_at FROM compliance_l2_log ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_research_kpis(self) -> list:
        """获取科研 KPI 数据（在研 PI 数、产品总数、报价单数）。

        返回:
            包含 kpi_name 和 value 的字典列表。
        """
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
        """获取 PI 来源分布统计。

        返回:
            包含 source 和 count 的字典列表。
        """
        try:
            self.db.execute("ALTER TABLE pi_profiles ADD COLUMN source TEXT NOT NULL DEFAULT ''")
        except Exception:  # noqa: BLE001  # expected when ALTER TABLE ADD COLUMN fails because column already exists
            pass  # 兼容操作：列已存在时跳过
        rows = self.db.execute(
            "SELECT COALESCE(NULLIF(source, ''), institution) as source, COUNT(*) as count FROM pi_profiles GROUP BY source ORDER BY count DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_product_match_stats(self) -> list:
        """获取产品匹配统计，按类别汇总总数和平均匹配分。

        返回:
            包含 category、total 和 avg_score 的字典列表。
        """
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
