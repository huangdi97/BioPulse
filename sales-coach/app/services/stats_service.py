"""统计服务模块，提供教练数据的聚合统计、趋势分析和多维对比。"""

import json
from collections import defaultdict
from typing import List

from sales_coach.app.repositories import StatsRepository
from sales_coach.app.services.base import BaseService


class StatsService(BaseService):
    """统计服务，提供全局统计、个人趋势、团队对比、雷达图及分类表现。"""

    def get_stats(self) -> dict:
        """获取全局教练统计数据。

        Returns:
            教练全局统计字典。
        """
        repo = StatsRepository(self.db)
        return repo.get_coach_stats()

    def get_user_trend(self, user_id: int, months: int = 6) -> List[dict]:
        """获取个人评分趋势（月度聚合）。

        Args:
            user_id: 用户ID。
            months: 回溯月数，默认6个月。

        Returns:
            月度评分趋势列表。
        """
        rows = self.db.execute(
            "SELECT score, created_at FROM coach_session "
            "WHERE created_by = ? AND score IS NOT NULL "
            "AND created_at >= date('now', '-' || ? || ' months') "
            "ORDER BY created_at ASC",
            (user_id, months),
        ).fetchall()
        monthly = defaultdict(list)
        for r in rows:
            month = r["created_at"][:7] if r["created_at"] else "unknown"
            monthly[month].append(r["score"])
        return [
            {
                "month": m,
                "avg_score": round(sum(scores) / len(scores), 1),
                "count": len(scores),
            }
            for m, scores in sorted(monthly.items())
        ]

    def get_team_comparison(self, team_id: int) -> dict:
        """获取团队对比数据。

        Args:
            team_id: 团队ID。

        Returns:
            包含平均分、最高分、最低分和标准差的字典。
        """
        rows = self.db.execute("SELECT score FROM coach_session WHERE score IS NOT NULL").fetchall()
        scores = [r["score"] for r in rows]
        if not scores:
            return {"avg": 0, "max": 0, "min": 0, "std": 0, "count": 0}
        avg = sum(scores) / len(scores)
        variance = sum((s - avg) ** 2 for s in scores) / len(scores)
        return {
            "avg": round(avg, 1),
            "max": max(scores),
            "min": min(scores),
            "std": round(variance**0.5, 1),
            "count": len(scores),
        }

    def get_radar_data(self, user_id: int) -> dict:
        """获取雷达图数据（各维度平均分）。

        Args:
            user_id: 用户ID。

        Returns:
            包含各维度平均分的字典。
        """
        rows = self.db.execute(
            "SELECT auto_assessment FROM coach_session WHERE created_by = ? AND auto_assessment IS NOT NULL",
            (user_id,),
        ).fetchall()
        dims = {
            "product_knowledge": [],
            "communication": [],
            "compliance": [],
            "objection_handling": [],
        }
        for r in rows:
            try:
                aa = json.loads(r["auto_assessment"])
                if isinstance(aa, dict) and "scores" in aa:
                    for k in dims:
                        if k in aa["scores"]:
                            dims[k].append(aa["scores"][k])
                elif isinstance(aa, dict):
                    for k in dims:
                        if k in aa:
                            dims[k].append(aa[k])
            except (json.JSONDecodeError, TypeError):
                pass
        return {k: round(sum(v) / len(v), 1) if v else 0 for k, v in dims.items()}

    def get_category_performance(self, user_id: int) -> List[dict]:
        """获取各类场景的表现对比。

        Args:
            user_id: 用户ID。

        Returns:
            按场景分类的表现数据列表。
        """
        rows = self.db.execute(
            "SELECT cs.scenario_id, cs.score, cs.auto_assessment, "
            "csc.title AS scenario_title, csc.category "
            "FROM coach_session cs "
            "LEFT JOIN coach_scenario csc ON cs.scenario_id = csc.id "
            "WHERE cs.created_by = ? AND cs.score IS NOT NULL",
            (user_id,),
        ).fetchall()
        grouped = defaultdict(list)
        for r in rows:
            key = r["category"] or r["scenario_title"] or "general"
            grouped[key].append(r["score"])
        return [
            {
                "category": cat,
                "avg_score": round(sum(scores) / len(scores), 1),
                "count": len(scores),
            }
            for cat, scores in sorted(grouped.items())
        ]
