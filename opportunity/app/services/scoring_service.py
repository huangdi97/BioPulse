"""评分服务，负责对商机和投标进行评分计算。"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException
from starlette import status

from opportunity.app.repositories import OpportunityRepository
from shared.base_service import BaseService

STAGE_SCORES = {
    "lead": 10,
    "qualification": 25,
    "proposal": 50,
    "negotiation": 75,
    "closed_won": 100,
    "closed_lost": 0,
}
DEFAULT_STAGE_SCORE = 5


"""线索评分引擎，基于阶段、概率、金额、时效性计算商机热度分。"""


class ScoringService(BaseService):
    """线索评分引擎：计算热度分、生成排行榜、手动设分、全量重算。"""

    def calculate_heat_score(
        self,
        stage: Optional[str],
        probability: Optional[int],
        estimated_value: Optional[float],
        updated_at: Optional[str],
    ) -> int:
        """根据阶段、概率、金额、时效性计算商机热度分。

        Args:
            stage: 商机阶段; probability: 成交概率; estimated_value: 预估金额; updated_at: 最近更新时间

        Returns:
            int: 热度评分（0-100）
        """
        stage_part = STAGE_SCORES.get(stage or "", DEFAULT_STAGE_SCORE)

        prob = probability if probability is not None else 0
        prob_part = min(prob * 0.3, 30)

        if estimated_value:
            value_part = min(estimated_value / 100000 * 10, 20)
        else:
            value_part = 0

        recency_part = 0
        if updated_at:
            try:
                clean = updated_at.replace("Z", "+00:00")
                updated_dt = datetime.fromisoformat(clean)
                if updated_dt.tzinfo is None:
                    updated_dt = updated_dt.replace(tzinfo=timezone.utc)
                days = (datetime.now(timezone.utc) - updated_dt).days
                recency_part = max(0, 20 - days)
            except (ValueError, TypeError):
                recency_part = 0

        return min(int(stage_part + prob_part + value_part + recency_part), 100)

    def leaderboard(
        self,
        page: int,
        page_size: int,
        stage: Optional[str] = None,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
    ) -> tuple:
        """分页查询热度排行榜。

        Args:
            page: 页码; page_size: 每页条数; stage: 可选阶段过滤; min_score: 可选最低分过滤; max_score: 可选最高分过滤

        Returns:
            tuple: (items, total, page, page_size, total_pages)
        """
        conditions: List[str] = []
        params: list = []

        if stage:
            conditions.append("stage = ?")
            params.append(stage)
        if min_score is not None:
            conditions.append("heat_score >= ?")
            params.append(min_score)
        if max_score is not None:
            conditions.append("heat_score <= ?")
            params.append(max_score)

        repo = OpportunityRepository(self._connection())
        return repo.paginate(
            page=page,
            page_size=page_size,
            conditions=conditions if conditions else None,
            params=params if params else None,
            order_by="heat_score DESC, id DESC",
        )

    def set_heat_score(self, opportunity_id: int, heat_score: int) -> dict:
        """手动设置商机热度分。

        Args:
            opportunity_id: 商机ID; heat_score: 热度评分

        Returns:
            dict: 更新后的商机记录
        """
        repo = OpportunityRepository(self._connection())
        row = repo.get_by_id(opportunity_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
        now = datetime.now(timezone.utc).isoformat()
        repo.update(opportunity_id, {"heat_score": heat_score, "updated_at": now})
        return dict(repo.get_by_id(opportunity_id))

    def recalculate(self) -> dict:
        """全量重新计算所有活跃商机的热度分。

        Returns:
            dict: 包含 total_updated、average_score、top_score、bottom_score 的统计结果
        """
        repo = OpportunityRepository(self._connection())
        rows = repo.list_all(conditions=["is_active = 1"])

        if not rows:
            return {
                "total_updated": 0,
                "average_score": 0.0,
                "top_score": 0,
                "bottom_score": 0,
            }

        scores: List[int] = []
        now = datetime.now(timezone.utc).isoformat()
        for r in rows:
            d = dict(r)
            score = self.calculate_heat_score(
                stage=d.get("stage"),
                probability=d.get("probability"),
                estimated_value=d.get("estimated_value"),
                updated_at=d.get("updated_at"),
            )
            repo.update(d["id"], {"heat_score": score, "updated_at": now})
            scores.append(score)

        return {
            "total_updated": len(scores),
            "average_score": round(sum(scores) / len(scores), 2),
            "top_score": max(scores),
            "bottom_score": min(scores),
        }
