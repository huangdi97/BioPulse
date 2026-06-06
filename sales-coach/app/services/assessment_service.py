"""评估服务模块，提供学员评估的创建、查询、更新、删除及自动评分功能。"""

import json
from datetime import datetime, timezone
from typing import Optional

from sales_coach.app.repositories import AssessmentRepository, SessionRepository
from sales_coach.app.services.base import BaseService

DEFAULT_WEIGHTS = {
    "product_knowledge": 0.3,
    "communication": 0.25,
    "compliance": 0.25,
    "objection_handling": 0.2,
}


class AssessmentService(BaseService):
    """学员评估服务，管理评估记录并支持自动评分与趋势分析。"""

    def create(self, body, user_id: int) -> dict:
        """创建学员评估记录。

        Args:
            body: 评估请求体。
            user_id: 创建者用户ID。

        Returns:
            包含新创建评估ID的字典。
        """
        conn = self._connection()
        try:
            repo = AssessmentRepository(conn)
            now = datetime.now(timezone.utc).isoformat()
            data = body.model_dump(exclude={"title"})
            extra = {"created_by": user_id, "created_at": now, "updated_at": now}
            assessment_id = repo.create(data, extra=extra)
            return {"id": assessment_id}
        finally:
            conn.close()

    def list(
        self,
        page: int,
        page_size: int,
        trainee_name: Optional[str] = None,
        current_level: Optional[str] = None,
        target_level: Optional[str] = None,
    ) -> tuple:
        """分页查询学员评估列表。

        Args:
            page: 页码。
            page_size: 每页条数。
            trainee_name: 按学员姓名筛选。
            current_level: 按当前等级筛选。
            target_level: 按目标等级筛选。

        Returns:
            (记录列表, 总条数) 元组。
        """
        conn = self._connection()
        try:
            repo = AssessmentRepository(conn)
            conditions = []
            params = []

            if trainee_name:
                conditions.append("trainee_name LIKE ?")
                params.append(f"%{trainee_name}%")
            if current_level:
                conditions.append("current_level = ?")
                params.append(current_level)
            if target_level:
                conditions.append("target_level = ?")
                params.append(target_level)

            return repo.paginate_active(page, page_size, conditions, params)
        finally:
            conn.close()

    def get_stats(self) -> dict:
        """获取评估统计数据。

        Returns:
            评估统计字典。
        """
        conn = self._connection()
        try:
            repo = AssessmentRepository(conn)
            return repo.get_stats()
        finally:
            conn.close()

    def get(self, assessment_id: int) -> dict:
        """获取单个评估详情。

        Args:
            assessment_id: 评估ID。

        Returns:
            评估详情字典，不存在或已删除则抛404。
        """
        conn = self._connection()
        try:
            repo = AssessmentRepository(conn)
            return dict(repo.get_active_or_404(assessment_id))
        finally:
            conn.close()

    def update(self, assessment_id: int, body) -> dict:
        """更新评估记录。

        Args:
            assessment_id: 评估ID。
            body: 更新数据。

        Returns:
            更新后的评估详情。
        """
        conn = self._connection()
        try:
            repo = AssessmentRepository(conn)
            repo.get_active_or_404(assessment_id)
            updates = body.model_dump(exclude_unset=True)
            if not updates:
                return dict(repo.get_by_id(assessment_id))
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            repo.update(assessment_id, updates)
            return dict(repo.get_by_id(assessment_id))
        finally:
            conn.close()

    def delete(self, assessment_id: int) -> None:
        """软删除评估记录。

        Args:
            assessment_id: 评估ID。
        """
        conn = self._connection()
        try:
            repo = AssessmentRepository(conn)
            repo.get_active_or_404(assessment_id)
            repo.soft_delete_assessment(assessment_id)
        finally:
            conn.close()

    @staticmethod
    def calculate_auto_score(dialogue_log: list, weights: Optional[dict] = None) -> dict:
        """根据对话日志自动计算评分。

        Args:
            dialogue_log: 对话日志列表。
            weights: 各维度权重字典，默认使用 DEFAULT_WEIGHTS。

        Returns:
            包含各维度评分和总分的字典。
        """
        if not weights:
            weights = DEFAULT_WEIGHTS
        rounds = len(dialogue_log) if dialogue_log else 0
        violations = 0
        user_entries = [e for e in dialogue_log if isinstance(e, dict) and e.get("role") == "user"]
        violations = sum(1 for e in user_entries if len(e.get("content", "")) < 3)
        product_knowledge = max(0, min(100, 65 + rounds * 2.5 - violations * 5))
        communication = max(0, min(100, 60 + rounds * 2 - violations * 3))
        compliance = max(0, min(100, 100 - violations * 15))
        objection_handling = max(0, min(100, 55 + rounds * 3 - violations * 4))
        scores = {
            "product_knowledge": round(product_knowledge, 1),
            "communication": round(communication, 1),
            "compliance": round(compliance, 1),
            "objection_handling": round(objection_handling, 1),
        }
        overall = sum(scores[k] * weights.get(k, 0.25) for k in scores)
        scores["overall"] = round(overall, 1)
        return {
            "scores": scores,
            "score_breakdown": json.dumps(scores),
        }

    def get_trend(self, user_id: int, limit: int = 10) -> list:
        """获取用户评分趋势。

        Args:
            user_id: 用户ID。
            limit: 返回记录条数上限。

        Returns:
            评分记录列表。
        """
        conn = self._connection()
        try:
            repo = SessionRepository(conn)
            rows = repo.db.execute(
                "SELECT id, score, created_at, module_id FROM coach_session WHERE created_by = ? AND score IS NOT NULL ORDER BY id DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_sessions(self, trainee_name: str) -> Optional[dict]:
        """根据学员姓名查询最近一次会话。

        Args:
            trainee_name: 学员姓名。

        Returns:
            会话详情字典，不存在则返回None。
        """
        conn = self._connection()
        try:
            row = conn.execute(
                "SELECT id, dialogue_log, compliance_violations, scenario_id FROM coach_session WHERE trainee_name = ? ORDER BY id DESC LIMIT 1",
                (trainee_name,),
            ).fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    def update_assessment_with_reflection(self, assessment_id: int, reflection: dict) -> dict:
        """将反思报告数据回写至评估记录。

        Args:
            assessment_id: 评估ID。
            reflection: 反思报告字典，含摘要、评分等。

        Returns:
            更新后的评估详情。
        """
        conn = self._connection()
        try:
            repo = AssessmentRepository(conn)
            repo.get_active_or_404(assessment_id)
            repo.update(
                assessment_id,
                {
                    "notes": json.dumps(
                        {
                            "reflection_summary": reflection.get("summary", {}),
                            "scores": reflection.get("scores", {}),
                        },
                        ensure_ascii=False,
                    ),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            return dict(repo.get_by_id(assessment_id))
        finally:
            conn.close()
