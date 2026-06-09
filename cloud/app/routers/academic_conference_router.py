"""Academic conference APIs."""

from fastapi import APIRouter

from cloud.app.schemas.academic_conference import (
    ConferenceCheckinRequest,
    ConferenceInviteRequest,
    Meeting,
    MeetingCreate,
)
from cloud.app.services.academic_conference_service import (
    checkin_meeting,
    create_meeting,
    get_analytics,
    invite_meeting,
)

router = APIRouter(prefix="/api/conference", tags=["线上学术会议"])


@router.post("", response_model=Meeting, tags=["线上学术会议"])
def conference_create(body: MeetingCreate) -> Meeting:
    return create_meeting(body)


@router.post("/{conference_id}/invite", response_model=Meeting, tags=["线上学术会议"])
def conference_invite(
    conference_id: str,
    body: ConferenceInviteRequest | None = None,
) -> Meeting:
    return invite_meeting(conference_id, body or ConferenceInviteRequest())


@router.post("/{conference_id}/checkin", response_model=Meeting, tags=["线上学术会议"])
def conference_checkin(
    conference_id: str,
    body: ConferenceCheckinRequest | None = None,
) -> Meeting:
    return checkin_meeting(conference_id, body or ConferenceCheckinRequest())


@router.get("/{conference_id}/analytics", tags=["线上学术会议"])
def conference_analytics(conference_id: str) -> dict:
    return get_analytics(conference_id)
