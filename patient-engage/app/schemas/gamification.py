"""患者游戏化激励模型。"""

from datetime import datetime

from pydantic import BaseModel, Field


class PointsBreakdown(BaseModel):
    """积分明细。"""

    action: str
    points: int
    date: datetime


class PatientPoints(BaseModel):
    """患者积分账户。"""

    patient_id: str
    total_points: int = 0
    points_breakdown: list[PointsBreakdown] = Field(default_factory=list)
    level: str = "Bronze"
    streak_days: int = 0


class RewardOption(BaseModel):
    """可兑换奖励。"""

    id: str
    name: str
    description: str
    points_required: int


class RedemptionRecord(BaseModel):
    """奖励兑换记录。"""

    id: str
    patient_id: str
    reward_id: str
    points_spent: int
    redeemed_at: datetime
    status: str = "success"


class RedeemRequest(BaseModel):
    """奖励兑换请求。"""

    patient_id: str
    reward_id: str
