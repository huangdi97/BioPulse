from datetime import date, timedelta

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

    def get_visit_trends(self) -> dict:
        today = date.today()
        dates = []
        counts = []
        pass_rates = []
        for i in range(30):
            day = today - timedelta(days=29 - i)
            dates.append(day.isoformat())
            count = 80 + int(40 * i / 29)
            counts.append(count)
            pass_rate = round(90.0 + 9.0 * i / 29, 1)
            pass_rates.append(pass_rate)
        return {"dates": dates, "counts": counts, "pass_rates": pass_rates}

    def get_team_ranks(self) -> dict:
        members = [
            {"name": "张伟", "visits": 328, "compliance_rate": 98.5, "deals": 45},
            {"name": "李娜", "visits": 305, "compliance_rate": 97.2, "deals": 42},
            {"name": "王强", "visits": 298, "compliance_rate": 96.8, "deals": 38},
            {"name": "刘芳", "visits": 285, "compliance_rate": 99.1, "deals": 36},
            {"name": "陈静", "visits": 272, "compliance_rate": 95.4, "deals": 33},
            {"name": "赵明", "visits": 260, "compliance_rate": 94.8, "deals": 30},
            {"name": "孙丽", "visits": 245, "compliance_rate": 93.5, "deals": 28},
            {"name": "周杰", "visits": 230, "compliance_rate": 92.1, "deals": 25},
        ]
        return {"ranks": members}

    def get_violations(self) -> dict:
        violations = [
            {
                "id": 1,
                "rep_name": "张伟",
                "type": "拜访记录缺失",
                "detail": "未能按时提交拜访报告",
                "severity": "high",
                "date": "2025-05-28",
                "status": "pending",
            },
            {
                "id": 2,
                "rep_name": "李娜",
                "type": "合规评分不达标",
                "detail": "产品推广材料未通过合规审核",
                "severity": "medium",
                "date": "2025-05-27",
                "status": "resolved",
            },
            {
                "id": 3,
                "rep_name": "王强",
                "type": "超次数拜访",
                "detail": "单日拜访次数超出规定上限",
                "severity": "low",
                "date": "2025-05-25",
                "status": "resolved",
            },
            {
                "id": 4,
                "rep_name": "刘芳",
                "type": "会议签到缺失",
                "detail": "学术会议未按要求签到",
                "severity": "medium",
                "date": "2025-05-24",
                "status": "pending",
            },
            {
                "id": 5,
                "rep_name": "陈静",
                "type": "费用报销异常",
                "detail": "差旅费用超出报销标准",
                "severity": "high",
                "date": "2025-05-22",
                "status": "pending",
            },
            {
                "id": 6,
                "rep_name": "赵明",
                "type": "拜访频次不足",
                "detail": "月度拜访量低于KPI要求",
                "severity": "low",
                "date": "2025-05-20",
                "status": "resolved",
            },
            {
                "id": 7,
                "rep_name": "孙丽",
                "type": "产品资料过期",
                "detail": "使用过期产品说明书进行推广",
                "severity": "high",
                "date": "2025-05-18",
                "status": "pending",
            },
            {
                "id": 8,
                "rep_name": "周杰",
                "type": "客户信息不完整",
                "detail": "拜访记录中客户信息缺失",
                "severity": "medium",
                "date": "2025-05-16",
                "status": "pending",
            },
            {
                "id": 9,
                "rep_name": "吴芳",
                "type": "未授权推广",
                "detail": "推广未获批产品适应症",
                "severity": "high",
                "date": "2025-05-15",
                "status": "pending",
            },
            {
                "id": 10,
                "rep_name": "郑浩",
                "type": "培训未完成",
                "detail": "合规培训未在规定期限内完成",
                "severity": "low",
                "date": "2025-05-12",
                "status": "resolved",
            },
        ]
        return {"violations": violations}

    def get_research_kpis(self) -> dict:
        kpis = [
            {"title": "在研项目", "value": 28, "change": 3, "icon": "flask"},
            {"title": "临床试验", "value": 12, "change": -1, "icon": "clipboard"},
            {"title": "发表论文", "value": 56, "change": 8, "icon": "file-text"},
            {"title": "专利申请", "value": 9, "change": 2, "icon": "award"},
        ]
        return {"kpis": kpis}

    def get_pi_sources(self) -> dict:
        pis = [
            {"name": "陈建国", "institution": "北京协和医院", "matches": 15, "last_activity": "2025-06-03"},
            {"name": "李明辉", "institution": "上海瑞金医院", "matches": 12, "last_activity": "2025-06-02"},
            {"name": "王秀英", "institution": "中山大学附属第一医院", "matches": 10, "last_activity": "2025-06-01"},
            {"name": "赵永强", "institution": "华西医院", "matches": 9, "last_activity": "2025-05-30"},
            {"name": "张淑芬", "institution": "解放军总医院", "matches": 8, "last_activity": "2025-05-29"},
            {"name": "刘国栋", "institution": "武汉同济医院", "matches": 7, "last_activity": "2025-05-28"},
        ]
        return {"pi_sources": pis}

    def get_product_match_stats(self) -> dict:
        categories = [
            {"category": "心血管", "total": 156, "matched": 142, "rate": 91},
            {"category": "肿瘤", "total": 128, "matched": 118, "rate": 92},
            {"category": "糖尿病", "total": 98, "matched": 89, "rate": 91},
            {"category": "抗感染", "total": 85, "matched": 80, "rate": 94},
        ]
        return {"categories": categories}
