import json
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    TrainingAttributionsRepository,
    TrainingModulesRepository,
    TrainingSessionsRepository,
)

DIFFICULTY_LEVELS = ["beginner", "medium", "advanced", "expert"]

MODULE_COLS = [
    "id",
    "title",
    "category",
    "difficulty",
    "content",
    "prerequisites",
    "passing_score",
    "estimated_minutes",
    "is_active",
    "created_by",
    "created_at",
    "updated_at",
]
SESSION_COLS = [
    "id",
    "user_id",
    "module_id",
    "score",
    "passed",
    "time_spent_seconds",
    "answers",
    "feedback",
    "difficulty_used",
    "next_difficulty",
    "completed_at",
    "created_at",
]
ATTR_COLS = [
    "id",
    "user_id",
    "training_session_id",
    "metric_name",
    "metric_before",
    "metric_after",
    "change_pct",
    "attribution_score",
    "confidence",
    "analysis",
    "period_days",
    "created_at",
]


class CoachAbility:
    @staticmethod
    def _rd(row, cols):
        if row is None:
            return None
        d = dict(row) if not isinstance(row, dict) else row
        for key in ("prerequisites", "answers"):
            if key in d and isinstance(d[key], str):
                d[key] = json.loads(d[key])
        return d

    @staticmethod
    def _calc_next_difficulty(score: float, current: str) -> str:
        idx = DIFFICULTY_LEVELS.index(current) if current in DIFFICULTY_LEVELS else 1
        if score >= 0.9 and idx < len(DIFFICULTY_LEVELS) - 1:
            return DIFFICULTY_LEVELS[idx + 1]
        if score <= 0.5 and idx > 0:
            return DIFFICULTY_LEVELS[idx - 1]
        return current

    def create_module(
        self,
        title: str,
        category: str,
        difficulty: str,
        content: str,
        prerequisites: list,
        passing_score: float,
        estimated_minutes: int,
        created_by: int,
    ) -> dict:
        modules_repo = TrainingModulesRepository(self.db)
        module_id = modules_repo.create(
            {
                "title": title,
                "category": category,
                "difficulty": difficulty,
                "content": content,
                "prerequisites": json.dumps(prerequisites, ensure_ascii=False),
                "passing_score": passing_score,
                "estimated_minutes": estimated_minutes,
                "created_by": created_by,
            }
        )
        row = modules_repo.get_by_id(module_id)
        return self._rd(row, MODULE_COLS)

    def list_modules(self, category: Optional[str] = None, difficulty: Optional[str] = None) -> list:
        modules_repo = TrainingModulesRepository(self.db)
        conditions = ["is_active=1"]
        params = []
        if category:
            conditions.append("category=?")
            params.append(category)
        if difficulty:
            conditions.append("difficulty=?")
            params.append(difficulty)
        rows = modules_repo.list_all(conditions=conditions, params=params, order_by="id ASC")
        return [self._rd(r, MODULE_COLS) for r in rows]

    def create_session(
        self,
        user_id: int,
        module_id: int,
        score: float,
        passed: int,
        time_spent_seconds: int,
        answers: list,
        feedback: str,
        difficulty_used: str,
    ) -> dict:
        modules_repo = TrainingModulesRepository(self.db)
        sessions_repo = TrainingSessionsRepository(self.db)

        mod = modules_repo.get_by_id(module_id)
        if not mod or not mod.get("is_active"):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Module not found")
        next_diff = self._calc_next_difficulty(score, difficulty_used)
        session_id = sessions_repo.create(
            {
                "user_id": user_id,
                "module_id": module_id,
                "score": score,
                "passed": passed,
                "time_spent_seconds": time_spent_seconds,
                "answers": json.dumps(answers, ensure_ascii=False),
                "feedback": feedback,
                "difficulty_used": difficulty_used,
                "next_difficulty": next_diff,
            }
        )
        row = sessions_repo.get_by_id(session_id)
        return self._rd(row, SESSION_COLS)

    def list_sessions(
        self,
        user_id: Optional[int] = None,
        module_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        sessions_repo = TrainingSessionsRepository(self.db)
        conditions = []
        params = []
        if user_id is not None:
            conditions.append("user_id=?")
            params.append(user_id)
        if module_id is not None:
            conditions.append("module_id=?")
            params.append(module_id)
        total, total_pages, rows = sessions_repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )
        return {
            "items": [self._rd(r, SESSION_COLS) for r in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_session(self, session_id: int) -> dict:
        sessions_repo = TrainingSessionsRepository(self.db)
        row = sessions_repo.get_by_id(session_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
        return self._rd(row, SESSION_COLS)

    def create_attribution(
        self,
        user_id: int,
        metric_name: str,
        metric_before: float,
        metric_after: float,
        period_days: int,
    ) -> dict:
        attrs_repo = TrainingAttributionsRepository(self.db)
        cp = round((metric_after - metric_before) / metric_before, 4) if metric_before else 0.0
        att_id = attrs_repo.create(
            {
                "user_id": user_id,
                "metric_name": metric_name,
                "metric_before": metric_before,
                "metric_after": metric_after,
                "change_pct": cp,
                "period_days": period_days,
            }
        )
        row = attrs_repo.get_by_id(att_id)
        return self._rd(row, ATTR_COLS)

    def list_attributions(self, user_id: Optional[int] = None, metric_name: Optional[str] = None) -> list:
        attrs_repo = TrainingAttributionsRepository(self.db)
        conditions = []
        params = []
        if user_id is not None:
            conditions.append("user_id=?")
            params.append(user_id)
        if metric_name:
            conditions.append("metric_name=?")
            params.append(metric_name)
        rows = attrs_repo.list_all(
            conditions=conditions or None,
            params=params or None,
            order_by="created_at DESC",
        )
        return [self._rd(r, ATTR_COLS) for r in rows]
