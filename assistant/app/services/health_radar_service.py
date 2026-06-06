"""健康雷达服务模块。"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from assistant.app.repositories import HealthRadarRepository
from assistant.app.services.base import BaseService


class HealthRadarService(BaseService):
    """健康雷达服务，提供患者健康评估的增删改查与统计分析。"""

    def create(self, body, user_id: int) -> dict:
        """创建健康评估记录。

        Args:
            body: 健康评估请求体; user_id: 用户ID

        Returns:
            dict: 包含新记录 id 的结果
        """
        repo = HealthRadarRepository(self.db)
        now = datetime.now(timezone.utc).isoformat()
        row_id = repo.create(
            {
                **body.model_dump(exclude_unset=True),
                "created_by": user_id,
                "created_at": now,
                "updated_at": now,
            },
        )
        return {"id": row_id}

    def list(
        self,
        page: int,
        page_size: int,
        patient_name: Optional[str] = None,
        score_min: Optional[int] = None,
        score_max: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> tuple:
        """分页查询健康评估列表。

        Args:
            page: 页码; page_size: 每页条数; patient_name: 可选患者姓名模糊查询; score_min: 可选最低分过滤; score_max: 可选最高分过滤; date_from: 可选起始日期过滤; date_to: 可选截止日期过滤

        Returns:
            tuple: (items, total, page, page_size, total_pages)
        """
        repo = HealthRadarRepository(self.db)
        conditions = ["is_active = 1"]
        params: list = []

        if patient_name:
            conditions.append("patient_name LIKE ?")
            params.append(f"%{patient_name}%")
        if score_min is not None:
            conditions.append("score >= ?")
            params.append(score_min)
        if score_max is not None:
            conditions.append("score <= ?")
            params.append(score_max)
        if date_from:
            conditions.append("assessment_date >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("assessment_date <= ?")
            params.append(date_to)

        return repo.paginate(page, page_size, conditions, params)

    def get_stats(self) -> dict:
        """获取健康评估统计数据，包括总分、均分、分布和趋势。

        Returns:
            dict: 包含 total_assessments、average_score、score_distribution、recent_trend 的统计信息
        """
        repo = HealthRadarRepository(self.db)
        total = repo.count(conditions=["is_active = 1"])

        avg_row = self.db.execute("SELECT AVG(score) FROM health_radar WHERE is_active = 1").fetchone()
        average_score = round(avg_row[0], 1) if avg_row[0] is not None else 0.0

        dist_rows = self.db.execute(
            """SELECT
                 CASE
                   WHEN score < 40 THEN 'high_risk'
                   WHEN score <= 70 THEN 'medium_risk'
                   ELSE 'low_risk'
                 END AS risk_level,
                 COUNT(*) AS cnt
               FROM health_radar
               WHERE is_active = 1
               GROUP BY risk_level"""
        ).fetchall()
        score_distribution = {"high_risk": 0, "medium_risk": 0, "low_risk": 0}
        for r in dist_rows:
            score_distribution[r["risk_level"]] = r["cnt"]

        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
        trend_rows = self.db.execute(
            """SELECT assessment_date,
                      AVG(score) AS avg_score,
                      COUNT(*) AS cnt
               FROM health_radar
               WHERE is_active = 1 AND assessment_date >= ?
               GROUP BY assessment_date
               ORDER BY assessment_date ASC""",
            (seven_days_ago,),
        ).fetchall()
        recent_trend = [
            {
                "date": r["assessment_date"],
                "avg_score": round(r["avg_score"], 1),
                "count": r["cnt"],
            }
            for r in trend_rows
        ]

        return {
            "total_assessments": total,
            "average_score": average_score,
            "score_distribution": score_distribution,
            "recent_trend": recent_trend,
        }

    def get(self, health_radar_id: int) -> dict:
        """根据ID获取健康评估详情。

        Args:
            health_radar_id: 健康评估记录ID

        Returns:
            dict: 健康评估记录详情
        """
        repo = HealthRadarRepository(self.db)
        return dict(repo.get_or_404(health_radar_id))

    def update(self, health_radar_id: int, body) -> dict:
        """更新健康评估记录。

        Args:
            health_radar_id: 健康评估记录ID; body: 更新数据请求体

        Returns:
            dict: 更新后的健康评估记录
        """
        repo = HealthRadarRepository(self.db)
        repo.get_or_404(health_radar_id)
        updates = body.model_dump(exclude_unset=True)
        if not updates:
            return dict(repo.get_by_id(health_radar_id))
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        repo.update(health_radar_id, updates)
        return dict(repo.get_by_id(health_radar_id))

    def delete(self, health_radar_id: int) -> None:
        """软删除健康评估记录。

        Args:
            health_radar_id: 健康评估记录ID
        """
        repo = HealthRadarRepository(self.db)
        repo.get_or_404(health_radar_id)
        repo.soft_delete(health_radar_id)
