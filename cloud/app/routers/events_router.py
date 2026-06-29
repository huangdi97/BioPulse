"""事件管理路由。"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from starlette import status

from cloud.app.services.events.events_service import EventService
from shared.auth_scope import require_scope
from shared.base import success


class _CreateEventRequest(BaseModel):
    name: str
    type: str
    date: str
    agenda: str
    hcp_ids: list[str]


class _InviteHcpsRequest(BaseModel):
    hcp_ids: list[str]


class _CheckInRequest(BaseModel):
    hcp_id: str


router = APIRouter(prefix="/api/v1/events", tags=["Events"])


@router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
    summary="创建事件",
    description="创建一条新的事件记录。",
)
def create_event(
    body: _CreateEventRequest,
    current_user: dict = Depends(require_scope("pharma")),
    service: EventService = Depends(),
):
    result = service.create_event(
        name=body.name,
        type=body.type,
        date=body.date,
        agenda=body.agenda,
        hcp_ids=body.hcp_ids,
    )
    return success(data=result)


@router.post(
    "/{id}/invite",
    status_code=status.HTTP_200_OK,
    summary="邀请HCP",
    description="向指定事件中添加受邀HCP。",
)
def invite_hcps(
    id: str,
    body: _InviteHcpsRequest,
    current_user: dict = Depends(require_scope("pharma")),
    service: EventService = Depends(),
):
    result = service.invite_hcps(event_id=id, hcp_ids=body.hcp_ids)
    return success(data=result)


@router.post(
    "/{id}/checkin",
    status_code=status.HTTP_200_OK,
    summary="签到",
    description="为指定事件中的HCP签到。",
)
def check_in(
    id: str,
    body: _CheckInRequest,
    current_user: dict = Depends(require_scope("pharma")),
    service: EventService = Depends(),
):
    result = service.check_in(event_id=id, hcp_id=body.hcp_id)
    return success(data=result)


@router.post(
    "/{id}/approve",
    status_code=status.HTTP_200_OK,
    summary="审批事件",
    description="审批指定事件。",
)
def approve_event(
    id: str,
    current_user: dict = Depends(require_scope("pharma")),
    service: EventService = Depends(),
):
    result = service.approve_event(event_id=id)
    return success(data=result)


@router.get(
    "/{id}/summary",
    status_code=status.HTTP_200_OK,
    summary="事件摘要",
    description="获取指定事件的汇总信息。",
)
def get_summary(
    id: str,
    current_user: dict = Depends(require_scope("pharma")),
    service: EventService = Depends(),
):
    result = service.get_summary(event_id=id)
    return success(data=result)
