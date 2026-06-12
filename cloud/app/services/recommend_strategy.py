"""推荐策略方法。"""

import math
from typing import Optional

from cloud.app.repositories import KgEntitiesRepository, RecommendationsRepository, UserBehaviorsRepository
from shared.base import PaginatedResponse


class RecommendStrategyMixin:
    """个性化推荐生成和推荐列表策略。"""

    def generate_recommendations(self, user_id: int, rec_types: list, limit: int) -> list:
        """Generate personalized recommendations for a user.

        Uses hot-action strategy if the user has >= 3 behaviors, otherwise falls back
        to knowledge-graph popularity.

        Args:
            user_id: The user's ID.
            rec_types: A list of recommendation types to cycle through.
            limit: Maximum number of recommendations to generate.

        Returns:
            A list of dicts representing the generated recommendation records.
        """
        behaviors_repo = UserBehaviorsRepository(self._connection())
        recs_repo = RecommendationsRepository(self._connection())
        kg_repo = KgEntitiesRepository(self._connection())
        behavior_count = behaviors_repo.count_by_user(user_id)
        results = []
        if behavior_count >= 3:
            top = behaviors_repo.top_action_by_user(user_id)
            if top:
                hot = behaviors_repo.top_targets_by_user_action(user_id, top["action_type"], limit)
                for i, t in enumerate(hot):
                    rt = rec_types[i % len(rec_types)]
                    rec_id = recs_repo.create(
                        {
                            "user_id": user_id,
                            "rec_type": rt,
                            "rec_target_id": t["target_id"],
                            "rec_title": t["target_id"],
                            "rec_reason": f"用户行为: {top['action_type']} 热度推荐",
                            "score": min(0.95, 0.5 + (i + 1) * 0.08),
                            "strategy_name": "hot-action",
                        }
                    )
                    results.append(recs_repo.get_by_id(rec_id))
        else:
            entities = kg_repo.top_active(limit)
            for i, e in enumerate(entities):
                rt = rec_types[i % len(rec_types)]
                rec_id = recs_repo.create(
                    {
                        "user_id": user_id,
                        "rec_type": rt,
                        "rec_target_id": e["entity_id"],
                        "rec_title": e["name"],
                        "rec_reason": f"知识图谱热门实体推荐: {e['entity_type']}",
                        "score": e["confidence"],
                        "strategy_name": "kg-popular",
                    }
                )
                results.append(recs_repo.get_by_id(rec_id))
        return results

    def list_recommendations(
        self,
        user_id: Optional[int] = None,
        rec_type: Optional[str] = None,
        clicked: Optional[int] = None,
        dismissed: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedResponse:
        """List recommendations with optional filtering and pagination.

        Args:
            user_id: Optional filter by user ID.
            rec_type: Optional filter by recommendation type.
            clicked: Optional filter by click status (1 for clicked, 0 otherwise).
            dismissed: Optional filter by dismiss status (1 for dismissed, 0 otherwise).
            limit: Maximum number of items to return.
            offset: Number of items to skip.

        Returns:
            A PaginatedResponse containing recommendation items.
        """
        recs_repo = RecommendationsRepository(self._connection())
        total, _, items = recs_repo.list_filtered(
            user_id=user_id,
            rec_type=rec_type,
            clicked=clicked,
            dismissed=dismissed,
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
