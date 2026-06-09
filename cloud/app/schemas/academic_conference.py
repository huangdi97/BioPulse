"""Academic conference schemas for cloud marketing automation."""

from enum import Enum

from pydantic import BaseModel, Field


class MeetingType(str, Enum):
    WEBINAR = "webinar"
    SATELLITE = "satellite"


class MeetingStatus(str, Enum):
    CREATED = "created"
    INVITED = "invited"
    LIVE = "live"
    CHECKED_IN = "checked_in"
    TRACKED = "tracked"
    COMPLIANCE_ARCHIVED = "compliance_archived"


class InteractiveFeature(BaseModel):
    qa: bool = Field(default=True, serialization_alias="q&a")
    poll: bool = True
    survey: bool = True
    handout: bool = True


class DataTrace(BaseModel):
    checkin_rate: float = Field(default=0.0, ge=0, le=100)
    average_stay_minutes: float = Field(default=0.0, ge=0)
    interaction_participation_rate: float = Field(default=0.0, ge=0, le=100)
    replay_views: int = Field(default=0, ge=0)


class Meeting(BaseModel):
    id: str
    title: str
    type: MeetingType
    date: str
    duration: int = Field(..., gt=0)
    speaker: str | None = None
    status: MeetingStatus
    interactive_features: InteractiveFeature = Field(default_factory=InteractiveFeature)
    data_trace: DataTrace = Field(default_factory=DataTrace)
    invited_count: int = 0
    checkin_count: int = 0
    end_to_end_trace: list[dict] = Field(default_factory=list)


class MeetingCreate(BaseModel):
    title: str
    type: MeetingType
    date: str
    duration: int = Field(..., gt=0)
    speaker: str | None = None
    interactive_features: InteractiveFeature = Field(default_factory=InteractiveFeature)


class ConferenceInviteRequest(BaseModel):
    invitee_ids: list[str] = Field(default_factory=list)
    channel: str = "wechat"
    operator: str = "marketing-automation"
    evidence: str = "invite-template-approved"


class ConferenceCheckinRequest(BaseModel):
    hcp_id: str = "hcp-001"
    name: str | None = None
    operator: str = "conference-platform"
    evidence: str = "checkin-token"
