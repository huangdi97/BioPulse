"""Recommendation filtering, sorting, and dashboard calculation utilities."""

import math
from typing import Optional

from cloud.app.repositories import (
    RecommendationsRepository,
    UserBehaviorsRepository,
    UserProfilesRepository,
    UsersRepository,
)
from shared.base import PaginatedResponse


def paginate_behaviors(
    db,
    user_id: Optional[int] = None,
    action_type: Optional[str] = None,
    target_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> PaginatedResponse:
    behaviors_repo = UserBehaviorsRepository(db)
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


def calc_dashboard_stats(db) -> dict:
    users_repo = UsersRepository(db)
    profiles_repo = UserProfilesRepository(db)
    behaviors_repo = UserBehaviorsRepository(db)
    recs_repo = RecommendationsRepository(db)
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
