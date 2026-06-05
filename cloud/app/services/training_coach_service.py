from typing import Optional

from cloud.app.services.base import BaseService

from .training_coach_assessor import CoachAssessor
from .training_coach_recommender import CoachRecommender


class TrainingCoachService(BaseService):
    def __init__(self, db):
        super().__init__(db)
        self._assessor = CoachAssessor(db)
        self._recommender = CoachRecommender(db)

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
        return self._assessor.create_module(
            title=title,
            category=category,
            difficulty=difficulty,
            content=content,
            prerequisites=prerequisites,
            passing_score=passing_score,
            estimated_minutes=estimated_minutes,
            created_by=created_by,
        )

    def list_modules(self, category: Optional[str] = None, difficulty: Optional[str] = None) -> list:
        return self._assessor.list_modules(category=category, difficulty=difficulty)

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
        return self._assessor.create_session(
            user_id=user_id,
            module_id=module_id,
            score=score,
            passed=passed,
            time_spent_seconds=time_spent_seconds,
            answers=answers,
            feedback=feedback,
            difficulty_used=difficulty_used,
        )

    def list_sessions(
        self,
        user_id: Optional[int] = None,
        module_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        return self._assessor.list_sessions(
            user_id=user_id,
            module_id=module_id,
            page=page,
            page_size=page_size,
        )

    def get_session(self, session_id: int) -> dict:
        return self._assessor.get_session(session_id=session_id)

    def recommend(self, user_id: int) -> dict:
        return self._recommender.recommend(user_id=user_id)

    def create_attribution(
        self,
        user_id: int,
        metric_name: str,
        metric_before: float,
        metric_after: float,
        period_days: int,
    ) -> dict:
        return self._assessor.create_attribution(
            user_id=user_id,
            metric_name=metric_name,
            metric_before=metric_before,
            metric_after=metric_after,
            period_days=period_days,
        )

    def list_attributions(self, user_id: Optional[int] = None, metric_name: Optional[str] = None) -> list:
        return self._assessor.list_attributions(user_id=user_id, metric_name=metric_name)

    def analyze_attribution(self, att_id: int) -> dict:
        return self._assessor.analyze_attribution(att_id=att_id)

    def dashboard(self) -> dict:
        return self._assessor.dashboard()
