"""培训教练推荐服务提供个性化培训内容推荐。"""

import json

from cloud.app.repositories import (
    TrainingModulesRepository,
    TrainingSessionsRepository,
)
from cloud.app.services.base import BaseService

DIFFICULTY_LEVELS = ["beginner", "medium", "advanced", "expert"]
VALID_DIFFICULTIES = {"beginner", "medium", "advanced", "expert"}

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


class CoachRecommender(BaseService):
    @staticmethod
    def _calc_next_difficulty(score: float, current: str) -> str:
        idx = DIFFICULTY_LEVELS.index(current) if current in DIFFICULTY_LEVELS else 1
        if score >= 0.9 and idx < len(DIFFICULTY_LEVELS) - 1:
            return DIFFICULTY_LEVELS[idx + 1]
        if score <= 0.5 and idx > 0:
            return DIFFICULTY_LEVELS[idx - 1]
        return current

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
    def _suggest_diff(avg_score: float) -> str:
        if avg_score >= 0.8:
            return "expert"
        if avg_score >= 0.6:
            return "advanced"
        if avg_score >= 0.4:
            return "medium"
        return "beginner"

    def recommend(self, user_id: int) -> dict:
        sessions_repo = TrainingSessionsRepository(self.db)
        modules_repo = TrainingModulesRepository(self.db)

        rows = sessions_repo.list_all(conditions=["user_id=?"], params=[user_id], order_by="created_at DESC")
        rows = rows[:3]
        if not rows:
            mods = modules_repo.list_all(conditions=["is_active=1"], order_by="id ASC")
            return {
                "recommended": self._rd(mods[0], MODULE_COLS) if mods else None,
                "reason": "no_history",
                "avg_score": None,
                "suggested_difficulty": "beginner",
            }
        avg_score = sum(r["score"] for r in rows) / len(rows)
        suggested = self._suggest_diff(avg_score)
        if suggested not in VALID_DIFFICULTIES:
            suggested = "beginner"
        completed_ids = [r["module_id"] for r in rows]
        ph = ",".join("?" * len(completed_ids))
        candidates = self.db.execute(
            f"SELECT * FROM training_modules WHERE is_active=1 AND id NOT IN ({ph}) "
            f"ORDER BY CASE WHEN difficulty='{suggested}' THEN 0 ELSE 1 END, id LIMIT 1",
            completed_ids,
        ).fetchall()
        rec = self._rd(candidates[0], MODULE_COLS) if candidates else None
        return {
            "recommended": rec,
            "reason": "based_on_score",
            "avg_score": round(avg_score, 2),
            "suggested_difficulty": suggested,
        }
