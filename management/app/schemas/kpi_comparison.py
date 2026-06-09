"""团队 KPI 对比看板数据模型。"""

from pydantic import BaseModel, Field


class TeamKPI(BaseModel):
    """团队 KPI 排名项。"""

    team_id: str = Field(..., description="团队 ID")
    team_name: str = Field(..., description="团队名称")
    compliance_rate: float = Field(..., ge=0, le=100, description="合规率")
    visit_completion_rate: float = Field(..., ge=0, le=100, description="拜访完成率")
    task_completion_rate: float = Field(..., ge=0, le=100, description="任务完成率")
    avg_engagement_score: float = Field(..., ge=0, le=100, description="平均互动评分")
    rank: int = Field(..., ge=1, description="排名")


class KPIHistoryPoint(BaseModel):
    """单个团队的周期 KPI 历史。"""

    period_label: str
    compliance_rate: float = Field(..., ge=0, le=100)
    visit_completion_rate: float = Field(..., ge=0, le=100)
    task_completion_rate: float = Field(..., ge=0, le=100)
    avg_engagement_score: float = Field(..., ge=0, le=100)
