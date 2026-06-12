"""推荐服务，负责用户画像管理、行为记录与个性化推荐生成。"""

import json
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    RecommendationsRepository,
    UserBehaviorsRepository,
    UserProfilesRepository,
)
from cloud.app.services.recommend_filter import calc_dashboard_stats, paginate_behaviors
from cloud.app.services.recommend_strategy import RecommendStrategyMixin
from shared.base import PaginatedResponse, validate_columns
from shared.base_service import BaseService
from shared.columns import TABLE_USER_PROFILES_COLS


class RecommendService(RecommendStrategyMixin, BaseService):
    """推荐服务，提供用户画像管理、行为记录、个性化推荐生成与仪表盘统计。"""

    def create_profile(
        self,
        user_id: int,
        persona_type: str,
        specialization: str,
        experience_level: str,
        preferred_content_types: list,
        custom_tags: list,
    ) -> dict:
        """Create or upsert a user recommendation profile."""
        pct = json.dumps(preferred_content_types, ensure_ascii=False)
        tags = json.dumps(custom_tags, ensure_ascii=False)
        profiles_repo = UserProfilesRepository(self._connection())
        row = profiles_repo.upsert_profile(user_id, persona_type, specialization, experience_level, pct, tags)
        return row

    def get_profile(self, user_id: int) -> dict:
        """Retrieve a user's recommendation profile.

        Raises:
            HTTPException: 404 if the profile is not found.
        """
        profiles_repo = UserProfilesRepository(self._connection())
        row = profiles_repo.get_by_user_id(user_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        return row

    def update_profile(
        self,
        user_id: int,
        persona_type: Optional[str] = None,
        specialization: Optional[str] = None,
        experience_level: Optional[str] = None,
        preferred_content_types: Optional[list] = None,
        custom_tags: Optional[list] = None,
    ) -> dict:
        """Update fields of an existing user recommendation profile.

        Raises:
            HTTPException: 404 if the profile is not found.
        """
        profiles_repo = UserProfilesRepository(self._connection())
        existing = profiles_repo.get_by_user_id(user_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        updates = {}
        for field in ("persona_type", "specialization", "experience_level"):
            v = locals().get(field)
            if v is not None:
                updates[field] = v
        if preferred_content_types is not None:
            updates["preferred_content_types"] = json.dumps(preferred_content_types, ensure_ascii=False)
        if custom_tags is not None:
            updates["custom_tags"] = json.dumps(custom_tags, ensure_ascii=False)
        if not updates:
            return existing
        updates["updated_at"] = "NOW()"
        validate_columns(updates, "user_profiles", TABLE_USER_PROFILES_COLS)
        profiles_repo.update(
            profiles_repo.db.execute("SELECT id FROM user_profiles WHERE user_id=?", (user_id,)).fetchone()["id"],
            {k: v for k, v in updates.items() if v != "NOW()"},
        )
        profiles_repo.db.execute("UPDATE user_profiles SET updated_at=NOW() WHERE user_id=?", (user_id,))
        profiles_repo.db.commit()
        row = profiles_repo.get_by_user_id(user_id)
        return row

    def log_behavior(
        self,
        user_id: int,
        action_type: str,
        target_type: str,
        target_id: str,
        metadata: dict,
        session_id: str,
        duration_seconds: int,
    ) -> dict:
        """Log a user behavior event for the recommendation engine."""
        behaviors_repo = UserBehaviorsRepository(self._connection())
        meta = json.dumps(metadata, ensure_ascii=False)
        row_id = behaviors_repo.create(
            {
                "user_id": user_id,
                "action_type": action_type,
                "target_type": target_type,
                "target_id": target_id,
                "metadata": meta,
                "session_id": session_id,
                "duration_seconds": duration_seconds,
            }
        )
        row = behaviors_repo.get_by_id(row_id)
        return row

    def behavior_history(
        self,
        user_id: Optional[int] = None,
        action_type: Optional[str] = None,
        target_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedResponse:
        """Retrieve paginated user behavior history with optional filters."""
        return paginate_behaviors(self.db, user_id, action_type, target_type, limit, offset)

    def mark_clicked(self, rec_id: int) -> None:
        """Mark a recommendation as clicked.

        Raises:
            HTTPException: 404 if the recommendation is not found.
        """
        recs_repo = RecommendationsRepository(self._connection())
        row = recs_repo.get_by_id(rec_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
        recs_repo.mark_clicked(rec_id)

    def mark_dismissed(self, rec_id: int) -> None:
        """Mark a recommendation as dismissed.

        Raises:
            HTTPException: 404 if the recommendation is not found.
        """
        recs_repo = RecommendationsRepository(self._connection())
        row = recs_repo.get_by_id(rec_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
        recs_repo.mark_dismissed(rec_id)

    def dashboard(self) -> dict:
        """Retrieve aggregated recommendation statistics for the dashboard."""
        return calc_dashboard_stats(self.db)
