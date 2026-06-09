"""AI排程请求与结果 schema。"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ScheduleRequest(BaseModel):
    rep_id: str = Field(..., min_length=1)
    date: str = Field(..., min_length=1)
    available_hours: List[str] = Field(default_factory=lambda: ["09:00", "17:00"])
    preferred_area: Optional[str] = None


class VisitSlot(BaseModel):
    hcp_id: str
    hcp_name: str
    address: str
    lat: float
    lng: float
    priority_score: float
    suggested_time: str
    visit_duration: int
    distance_from_prev: float


class ScheduleResult(BaseModel):
    optimized_visits: List[VisitSlot] = Field(default_factory=list)
    total_distance: float = 0
    total_time: int = 0
