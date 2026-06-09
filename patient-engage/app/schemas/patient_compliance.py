"""患者小程序用药提醒与依从性模型。"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PatientReminder(BaseModel):
    """患者用药提醒。"""

    id: str
    patient_id: str
    drug_name: str
    dosage: str = ""
    schedule: dict[str, Any] = Field(default_factory=dict)
    next_reminder: datetime
    status: str = "active"


class CheckInRecord(BaseModel):
    """患者用药打卡记录。"""

    id: str
    patient_id: str
    reminder_id: str
    checkin_time: datetime
    confirmed: bool = True


class ComplianceReport(BaseModel):
    """患者依从性报告。"""

    patient_id: str
    adherence_rate: float
    missed_doses: int
    weekly_report: list[dict[str, Any]]
    period: str


class ReminderCreateRequest(BaseModel):
    """创建提醒请求。"""

    patient_id: str
    drug: str | None = None
    drug_name: str | None = None
    dosage: str = ""
    schedule: dict[str, Any] = Field(default_factory=dict)


class CheckInRequest(BaseModel):
    """用药打卡请求。"""

    reminder_id: str
    confirmed: bool = True
