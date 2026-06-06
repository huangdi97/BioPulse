"""场景筛选模块，按分类或难度从固定场景中筛选匹配项。"""

from typing import List

from .scenario_fetcher import FIXED_SCENARIOS


class ScenarioLoader:
    def get_scenarios_by_category(self, category: str) -> List[dict]:
        """Return all fixed scenarios matching the given category."""
        return [s for s in FIXED_SCENARIOS if s["category"] == category]

    def get_scenario_by_difficulty(self, difficulty: str) -> List[dict]:
        """Return all fixed scenarios matching the given difficulty level."""
        return [s for s in FIXED_SCENARIOS if s["difficulty"] == difficulty]
