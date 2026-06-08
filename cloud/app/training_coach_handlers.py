"""培训教练路由的请求与响应模型。"""

from pydantic import BaseModel


class ModuleCreate(BaseModel):
    title: str
    category: str = "compliance"
    difficulty: str = "medium"
    content: str = ""
    prerequisites: list = []
    passing_score: float = 0.7
    estimated_minutes: int = 15


class SessionCreate(BaseModel):
    user_id: int
    module_id: int
    score: float = 0.0
    passed: int = 0
    time_spent_seconds: int = 0
    answers: list = []
    feedback: str = ""
    difficulty_used: str = "medium"


class AttributionCreate(BaseModel):
    user_id: int
    metric_name: str
    metric_before: float = 0.0
    metric_after: float = 0.0
    period_days: int = 30
