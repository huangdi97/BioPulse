"""Academic meeting workflow schemas."""

from enum import Enum

from pydantic import BaseModel, Field


class MeetingType(str, Enum):
    WEBINAR = "webinar"
    SATELLITE = "satellite"


class MeetingStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    LIVE = "live"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InvitationStatus(str, Enum):
    INVITED = "invited"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class Meeting(BaseModel):
    id: str
    title: str
    type: MeetingType
    date: str
    duration: int = Field(..., gt=0)
    speaker: str
    status: MeetingStatus = MeetingStatus.SCHEDULED


class MeetingCreate(BaseModel):
    title: str
    type: MeetingType
    date: str
    duration: int = Field(..., gt=0)
    speaker: str


class MeetingInvitation(BaseModel):
    id: str
    meeting_id: str
    hcp_id: str
    status: InvitationStatus = InvitationStatus.INVITED


class MeetingInviteCreate(BaseModel):
    hcp_id: str
    status: InvitationStatus = InvitationStatus.INVITED


class MeetingCheckIn(BaseModel):
    id: str
    meeting_id: str
    hcp_id: str
    checkin_time: str
    channel: str = "online"


class MeetingCheckInCreate(BaseModel):
    hcp_id: str
    checkin_time: str | None = None
    channel: str = "online"


class MeetingContent(BaseModel):
    id: str
    meeting_id: str
    title: str
    content_type: str = "slide"
    url: str = ""
    pushed_to: list[str] = Field(default_factory=list)


class MeetingContentCreate(BaseModel):
    title: str
    content_type: str = "slide"
    url: str = ""
    hcp_ids: list[str] = Field(default_factory=list)


class MeetingEffectiveness(BaseModel):
    meeting_id: str
    invited_count: int
    checked_in_count: int
    content_push_count: int
    attendance_rate: float
    effectiveness_score: int = Field(..., ge=0, le=100)


class ComplianceTrace(BaseModel):
    id: str
    meeting_id: str
    action: str
    detail: str
    created_at: str
