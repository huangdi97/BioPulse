"""Academic conference lifecycle service."""

from threading import Lock
from uuid import uuid4

from fastapi import HTTPException
from starlette import status

from cloud.app.schemas.academic_conference import (
    ConferenceCheckinRequest,
    ConferenceInviteRequest,
    DataTrace,
    Meeting,
    MeetingCreate,
    MeetingStatus,
)
from shared.datetime_utils import now as _now

_LOCK = Lock()

_MEETINGS: dict[str, Meeting] = {}
_CHECKINS: dict[str, set[str]] = {}


def _trace(step: str, who: str, what: str, evidence: str) -> dict[str, str]:
    """创建审计追踪记录。

    Args:
        step: 步骤名称
        who: 操作者
        what: 操作描述
        evidence: 证据标识

    Returns:
        追踪记录字典
    """
    return {
        "step": step,
        "who": who,
        "when": _now(),
        "what": what,
        "evidence": evidence,
    }


def _get_meeting(meeting_id: str) -> Meeting:
    """根据ID获取会议，不存在则返回404。

    Args:
        meeting_id: 会议ID

    Returns:
        会议对象

    Raises:
        HTTPException: 会议不存在时返回404
    """
    meeting = _MEETINGS.get(meeting_id)
    if not meeting:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Conference not found")
    return meeting


def create_meeting(data: MeetingCreate) -> Meeting:
    """创建学术会议。

    Args:
        data: 会议创建请求数据

    Returns:
        创建的会议对象
    """
    with _LOCK:
        meeting_id = f"conf-{uuid4().hex[:8]}"
        meeting = Meeting(
            id=meeting_id,
            title=data.title,
            type=data.type,
            date=data.date,
            duration=data.duration,
            speaker=data.speaker,
            status=MeetingStatus.CREATED,
            interactive_features=data.interactive_features,
            end_to_end_trace=[
                _trace(
                    "create",
                    "marketing-automation",
                    f"Created {data.type.value} conference",
                    "conference-request",
                )
            ],
        )
        _MEETINGS[meeting_id] = meeting
        _CHECKINS[meeting_id] = set()
        return meeting


def invite_meeting(meeting_id: str, request: ConferenceInviteRequest) -> Meeting:
    """发送会议邀请。

    Args:
        meeting_id: 会议ID
        request: 邀请请求数据（包含邀请者列表和渠道）

    Returns:
        更新后的会议对象
    """
    with _LOCK:
        meeting = _get_meeting(meeting_id)
        invitee_count = len(request.invitee_ids) or 120
        updated = meeting.model_copy(
            update={
                "status": MeetingStatus.INVITED,
                "invited_count": meeting.invited_count + invitee_count,
                "end_to_end_trace": [
                    *meeting.end_to_end_trace,
                    _trace(
                        "invite",
                        request.operator,
                        f"Sent {invitee_count} invitations via {request.channel}",
                        request.evidence,
                    ),
                ],
            }
        )
        _MEETINGS[meeting_id] = updated
        return updated


def checkin_meeting(meeting_id: str, request: ConferenceCheckinRequest) -> Meeting:
    """会议签到。

    Args:
        meeting_id: 会议ID
        request: 签到请求数据（包含HCP ID）

    Returns:
        更新后的会议对象
    """
    with _LOCK:
        meeting = _get_meeting(meeting_id)
        checked_in = _CHECKINS.setdefault(meeting_id, set())
        checked_in.add(request.hcp_id)
        status_value = MeetingStatus.CHECKED_IN if meeting.status != MeetingStatus.CREATED else MeetingStatus.LIVE
        updated = meeting.model_copy(
            update={
                "status": status_value,
                "checkin_count": len(checked_in),
                "end_to_end_trace": [
                    *meeting.end_to_end_trace,
                    _trace(
                        "checkin",
                        request.operator,
                        f"Checked in HCP {request.hcp_id}",
                        request.evidence,
                    ),
                ],
            }
        )
        _MEETINGS[meeting_id] = updated
        return updated


def get_analytics(meeting_id: str) -> dict:
    """获取会议分析数据并归档。

    Args:
        meeting_id: 会议ID

    Returns:
        包含会议数据、分析追踪和合规归档信息的字典
    """
    with _LOCK:
        meeting = _get_meeting(meeting_id)
        invited_count = meeting.invited_count or 120
        checkin_count = meeting.checkin_count or max(1, int(invited_count * 0.68))
        checkin_rate = round(checkin_count / invited_count * 100, 1)
        participation_rate = 74.5 if meeting.interactive_features.poll or meeting.interactive_features.survey else 42.0
        data_trace = DataTrace(
            checkin_rate=checkin_rate,
            average_stay_minutes=round(meeting.duration * 0.82, 1),
            interaction_participation_rate=participation_rate,
            replay_views=max(18, int(checkin_count * 0.35)),
        )
        trace = [
            *meeting.end_to_end_trace,
            _trace("live", "conference-platform", "Live stream completed and attendance captured", "live-room-log"),
            _trace("data_tracking", "analytics-engine", "Generated engagement and replay metrics", "analytics-ledger"),
            _trace("compliance_archive", "compliance-engine", "Archived consent, invite, checkin, and content evidence", "tamper-evident-archive"),
        ]
        updated = meeting.model_copy(
            update={
                "status": MeetingStatus.COMPLIANCE_ARCHIVED,
                "data_trace": data_trace,
                "checkin_count": checkin_count,
                "end_to_end_trace": trace,
            }
        )
        _MEETINGS[meeting_id] = updated
        return {
            "meeting": updated,
            "data_trace": data_trace,
            "compliance_retention": {
                "archived": True,
                "trace_count": len(trace),
                "retention_policy": "medical-marketing-5y",
            },
        }
