"""教练建议生成方法，包含训练归因功能。"""

from typing import Optional

from cloud.app.repositories import TrainingAttributionsRepository


class CoachSuggestionMixin:
    """教练建议生成方法，提供训练归因管理。"""

    def create_attribution(
        self,
        user_id: int,
        metric_name: str,
        metric_before: float,
        metric_after: float,
        period_days: int,
    ) -> dict:
        attrs_repo = TrainingAttributionsRepository(self._connection())
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
        return self._rd(
            row,
            [
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
            ],
        )

    def list_attributions(self, user_id: Optional[int] = None, metric_name: Optional[str] = None) -> list:
        attrs_repo = TrainingAttributionsRepository(self._connection())
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
        return [
            self._rd(
                r,
                [
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
                ],
            )
            for r in rows
        ]
