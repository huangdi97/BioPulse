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
        conn = self._connection()
        try:
            repo = AssessmentRepository(conn)
            return repo.get_stats()
        finally:
            conn.close()

    def get(self, assessment_id: int) -> dict:
        conn = self._connection()
        try:
            repo = AssessmentRepository(conn)
            return dict(repo.get_active_or_404(assessment_id))
        finally:
            conn.close()

    def update(self, assessment_id: int, body) -> dict:
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
        conn = self._connection()
        try:
            repo = AssessmentRepository(conn)
            repo.get_active_or_404(assessment_id)
            repo.soft_delete_assessment(assessment_id)
        finally:
            conn.close()

    @staticmethod
    def calculate_auto_score(dialogue_log: list, weights: Optional[dict] = None) -> dict:
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
