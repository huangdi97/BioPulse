"""教练能力服务，管理培训模块、培训记录与培训归因。"""

import json
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import TrainingModulesRepository, TrainingSessionsRepository
from cloud.app.services.coach_suggestion import CoachSuggestionMixin

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


class CoachAbility(CoachSuggestionMixin):
    """教练能力类，提供培训模块与培训记录的创建、查询及难度自适应。"""

    @staticmethod
    def _rd(row, cols):
        """将行数据做JSON字段反序列化。"""
        if row is None:
            return None
        d = dict(row) if not isinstance(row, dict) else row
        for key in ("prerequisites", "answers"):
            if key in d and isinstance(d[key], str):
                d[key] = json.loads(d[key])
        return d

    @staticmethod
    def _calc_next_difficulty(score: float, current: str) -> str:
        """根据得分计算下一难度等级。"""
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
        """创建培训模块。"""
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
        """按分类和难度列出培训模块。"""
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
        """创建培训记录并计算下一难度。"""
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
        """分页查询培训记录。"""
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
        """获取培训记录详情。"""
        sessions_repo = TrainingSessionsRepository(self.db)
        row = sessions_repo.get_by_id(session_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found")
        return self._rd(row, SESSION_COLS)
