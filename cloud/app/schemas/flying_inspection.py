"""飞检准备度仪表盘数据模型。"""

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class ChecklistStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CONFIRMED = "confirmed"


class InspectionChecklist(BaseModel):
    id: str
    category: str
    item: str
    status: ChecklistStatus
    deadline: str
    assignee: str
    remark: str = ""


class InspectionTask(BaseModel):
    id: str
    title: str
    description: str
    assignee: str
    deadline: str
    status: TaskStatus


class InspectionDashboard(BaseModel):
    self_check_rate: float
    overdue_count: int
    history_records: List[dict]
    score: int = Field(..., ge=0, le=100)
