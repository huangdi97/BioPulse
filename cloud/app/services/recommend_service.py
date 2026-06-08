"""推荐服务，负责用户画像管理、行为记录与个性化推荐生成。"""

import json
import math
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    RecommendationsRepository,
    UserBehaviorsRepository,
    UserProfilesRepository,
    UsersRepository,
)
from cloud.app.services.base import BaseService
from cloud.app.services.recommend_strategy import RecommendStrategyMixin
from shared.base import PaginatedResponse, validate_columns
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
        """Create or upsert a user recommendation profile.

        Args:
            user_id: The user's ID.
            persona_type: The user's persona type.
            specialization: The user's specialization.
            experience_level: The user's experience level.
            preferred_content_types: A list of preferred content types.
            custom_tags: A list of custom tags for the user profile.

        Returns:
            A dict representing the upserted profile row.
        """
        pct = json.dumps(preferred_content_types, ensure_ascii=False)
        tags = json.dumps(custom_tags, ensure_ascii=False)
        profiles_repo = UserProfilesRepository(self.db)
        row = profiles_repo.upsert_profile(user_id, persona_type, specialization, experience_level, pct, tags)
        return row

    def get_profile(self, user_id: int) -> dict:
        """Retrieve a user's recommendation profile.

        Args:
            user_id: The user's ID.

        Returns:
            A dict representing the user profile.

        Raises:
            HTTPException: 404 if the profile is not found.
        """
        profiles_repo = UserProfilesRepository(self.db)
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

        Args:
            user_id: The user's ID.
            persona_type: Optional new persona type.
            specialization: Optional new specialization.
            experience_level: Optional new experience level.
            preferred_content_types: Optional new list of preferred content types.
            custom_tags: Optional new list of custom tags.

        Returns:
            A dict representing the updated profile.

        Raises:
            HTTPException: 404 if the profile is not found.
        """
        profiles_repo = UserProfilesRepository(self.db)
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
        """Log a user behavior event for the recommendation engine.

        Args:
            user_id: The user's ID.
            action_type: The type of action (e.g. "view", "click", "download").
            target_type: The type of target (e.g. "article", "protocol").
            target_id: The target's unique identifier.
            metadata: Additional metadata about the behavior event.
            session_id: The session identifier.
            duration_seconds: Duration of the interaction in seconds.

        Returns:
            A dict representing the created behavior record.
        """
        behaviors_repo = UserBehaviorsRepository(self.db)
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
        """Retrieve paginated user behavior history with optional filters.

        Args:
            user_id: Optional filter by user ID.
            action_type: Optional filter by action type.
            target_type: Optional filter by target type.
            limit: Maximum number of items to return.
            offset: Number of items to skip.

        Returns:
            A PaginatedResponse containing behavior items.
        """
        behaviors_repo = UserBehaviorsRepository(self.db)
        total, _, items = behaviors_repo.list_filtered(
            user_id=user_id,
            action_type=action_type,
            target_type=target_type,
            limit=limit,
            offset=offset,
        )
        page = offset // max(limit, 1) + 1
        total_pages = math.ceil(total / max(limit, 1))
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=limit,
            total_pages=total_pages,
        )

    def mark_clicked(self, rec_id: int) -> None:
        """Mark a recommendation as clicked.

        Args:
            rec_id: The ID of the recommendation.

        Raises:
            HTTPException: 404 if the recommendation is not found.
        """
        recs_repo = RecommendationsRepository(self.db)
        row = recs_repo.get_by_id(rec_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
        recs_repo.mark_clicked(rec_id)

    def mark_dismissed(self, rec_id: int) -> None:
        """Mark a recommendation as dismissed.

        Args:
            rec_id: The ID of the recommendation.

        Raises:
            HTTPException: 404 if the recommendation is not found.
        """
        recs_repo = RecommendationsRepository(self.db)
        row = recs_repo.get_by_id(rec_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
        recs_repo.mark_dismissed(rec_id)

    def dashboard(self) -> dict:
        """Retrieve aggregated recommendation statistics for the dashboard.

        Returns:
            A dict with total_users, total_profiles, total_behaviors, total_recommendations,
            total_clicked, total_dismissed, click_rate, dismiss_rate, top_actions, and rec_by_type.
        """
        users_repo = UsersRepository(self.db)
        profiles_repo = UserProfilesRepository(self.db)
        behaviors_repo = UserBehaviorsRepository(self.db)
        recs_repo = RecommendationsRepository(self.db)
        total_users = users_repo.count_all()
        total_profiles = profiles_repo.count()
        total_behaviors = behaviors_repo.count()
        total_recs = recs_repo.count_all()
        total_clicked = recs_repo.count_clicked()
        total_dismissed = recs_repo.count_dismissed()
        click_rate = round(total_clicked / total_recs, 4) if total_recs > 0 else 0.0
        dismiss_rate = round(total_dismissed / total_recs, 4) if total_recs > 0 else 0.0
        top_actions = behaviors_repo.top_actions_global(10)
        rec_by_type = recs_repo.count_by_rec_type()
        return {
            "total_users": total_users,
            "total_profiles": total_profiles,
            "total_behaviors": total_behaviors,
            "total_recommendations": total_recs,
            "total_clicked": total_clicked,
            "total_dismissed": total_dismissed,
            "click_rate": click_rate,
            "dismiss_rate": dismiss_rate,
            "top_actions": top_actions,
            "rec_by_type": rec_by_type,
        }
