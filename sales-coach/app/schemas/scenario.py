"""场景增强数据模型。"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

DifficultyLevel = Literal["beginner", "intermediate", "advanced"]


class Scenario(BaseModel):
    """销售训练场景。"""

    id: Optional[int] = None
    title: str
    role_setting: Optional[str] = None
    goal: Optional[str] = None
    difficulty: Optional[str] = "medium"
    difficulty_level: DifficultyLevel = "intermediate"
    prerequisites: list[str] = Field(default_factory=list)
    category: Optional[str] = None
    content: Optional[str] = None
    tips: Optional[str] = None


class ScenarioRecommendation(BaseModel):
    """场景推荐结果。"""

    user_id: str
    average_score: float
    difficulty_level: DifficultyLevel
    scenario: Scenario
