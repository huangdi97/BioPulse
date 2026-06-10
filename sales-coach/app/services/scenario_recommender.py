"""场景难度推荐服务。"""

import re
from typing import Optional

from sales_coach.app.scenario_library import FIXED_SCENARIOS
from sales_coach.app.schemas.scenario import Scenario, ScenarioRecommendation
from shared.base_service import BaseService

_LEVEL_TO_DIFFICULTY = {
    "beginner": "easy",
    "intermediate": "medium",
    "advanced": "hard",
}

_PREREQUISITES = {
    "beginner": ["完成合规基础培训", "熟悉产品基础信息"],
    "intermediate": ["掌握基础拜访流程", "能引用核心临床数据"],
    "advanced": ["完成异议处理训练", "熟悉竞品与合规边界"],
}


def recommend_scenario(user_id: str) -> ScenarioRecommendation:
    """基于历史评分推荐匹配难度的训练场景。"""

    service = ScenarioRecommenderService()
    return service.recommend_scenario(user_id)


class ScenarioRecommenderService(BaseService):
    """根据用户历史表现推荐训练场景。"""

    def recommend_scenario(self, user_id: str) -> ScenarioRecommendation:
        conn = self._connection()
        try:
            average_score = self._average_score(conn, user_id)
            difficulty_level = _score_to_level(average_score)
            scenario = self._select_scenario(conn, difficulty_level)
            return ScenarioRecommendation(
                user_id=user_id,
                average_score=average_score,
                difficulty_level=difficulty_level,
                scenario=scenario,
            )
        finally:
            self._close_connection(conn)

    def _average_score(self, conn, user_id: str) -> float:
        numeric_id = _parse_numeric_id(user_id)
        if numeric_id is None:
            return 0.0
        row = conn.execute(
            "SELECT AVG(score) AS avg_score FROM coach_session WHERE created_by = ? AND score IS NOT NULL",
            (numeric_id,),
        ).fetchone()
        return round(float(row["avg_score"] or 0), 1) if row else 0.0

    def _select_scenario(self, conn, difficulty_level: str) -> Scenario:
        target_difficulty = _LEVEL_TO_DIFFICULTY[difficulty_level]
        row = conn.execute(
            "SELECT id, title, role_setting, goal, difficulty, category, content, tips "
            "FROM coach_scenario WHERE is_active = 1 AND difficulty = ? "
            "ORDER BY id DESC LIMIT 1",
            (target_difficulty,),
        ).fetchone()
        if row:
            data = dict(row)
        else:
            data = next(
                (item for item in FIXED_SCENARIOS if item.get("difficulty") == target_difficulty),
                FIXED_SCENARIOS[0],
            ).copy()
        data["difficulty_level"] = difficulty_level
        data["prerequisites"] = _PREREQUISITES[difficulty_level]
        return Scenario(**data)

    def _close_connection(self, conn) -> None:
        if not hasattr(self, "db") or self.db is not conn:
            conn.close()


def _score_to_level(score: float) -> str:
    if score < 60:
        return "beginner"
    if score <= 80:
        return "intermediate"
    return "advanced"


def _parse_numeric_id(user_id: str) -> Optional[int]:
    match = re.search(r"(\d+)$", str(user_id))
    if not match:
        return None
    return int(match.group(1))
