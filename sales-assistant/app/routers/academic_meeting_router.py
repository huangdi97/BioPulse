"""Academic meeting integration APIs."""

from fastapi import APIRouter
from starlette import status

from sales_assistant.app.schemas.academic_meeting import (
    Meeting,
    MeetingCheckIn,
    MeetingCheckInCreate,
    MeetingContent,
    MeetingContentCreate,
    MeetingCreate,
    MeetingEffectiveness,
    MeetingInvitation,
    MeetingInviteCreate,
)
from sales_assistant.app.services.academic_meeting_service import (
    checkin_hcp,
    create_meeting,
    delete_meeting,
    get_effectiveness,
    invite_hcp,
    list_meetings,
    push_content,
    update_meeting,
)

router = APIRouter(prefix="/api/meetings", tags=["学术会议"])


@router.get("", response_model=list[Meeting], tags=["学术会议"])
def get_meetings() -> list[Meeting]:
    return list_meetings()


@router.post("", response_model=Meeting, status_code=status.HTTP_201_CREATED, tags=["学术会议"])
def post_meeting(body: MeetingCreate) -> Meeting:
    return create_meeting(body)


@router.put("/{id}", response_model=Meeting, tags=["学术会议"])
def put_meeting(id: str, body: MeetingCreate) -> Meeting:
    return update_meeting(id, body)


@router.delete("/{id}", tags=["学术会议"])
def remove_meeting(id: str) -> dict[str, str]:
    return delete_meeting(id)


@router.post("/{id}/invite", response_model=MeetingInvitation, tags=["学术会议"])
def invite(id: str, body: MeetingInviteCreate) -> MeetingInvitation:
    return invite_hcp(id, body)


@router.post("/{id}/checkin", response_model=MeetingCheckIn, tags=["学术会议"])
def checkin(id: str, body: MeetingCheckInCreate) -> MeetingCheckIn:
    return checkin_hcp(id, body)


@router.post("/{id}/content", response_model=MeetingContent, tags=["学术会议"])
def content(id: str, body: MeetingContentCreate) -> MeetingContent:
    return push_content(id, body)


@router.get("/{id}/effectiveness", response_model=MeetingEffectiveness, tags=["学术会议"])
def effectiveness(id: str) -> MeetingEffectiveness:
    return get_effectiveness(id)
