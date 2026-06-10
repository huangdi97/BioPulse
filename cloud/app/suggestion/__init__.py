"""销售建议 Agent 模块，提供规划、收集、推荐与 Pre-call Brief 生成能力。"""

from .brief import Brief, BriefGenerator
from .collector import CollectionResult, InfoCollector
from .planner import CollectionPlan, CollectionStep, InfoCollectionPlanner
from .recommender import Strategy, StrategyRecommender, StrategySet

__all__ = [
    "Brief",
    "BriefGenerator",
    "CollectionPlan",
    "CollectionResult",
    "CollectionStep",
    "InfoCollectionPlanner",
    "InfoCollector",
    "Strategy",
    "StrategyRecommender",
    "StrategySet",
]
