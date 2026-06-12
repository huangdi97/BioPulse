"""Academic meeting workflow service."""

from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4

from fastapi import HTTPException
from starlette import status

from sales_assistant.app.schemas.academic_meeting import (
    ComplianceTrace,
    Meeting,
    MeetingCheckIn,
    MeetingCheckInCreate,
    MeetingContent,
    MeetingContentCreate,
    MeetingCreate,
    MeetingEffectiveness,
    MeetingInvitation,
    MeetingInviteCreate,
    MeetingStatus,
)

_MEETINGS: dict[str, Meeting] = {}
_INVITATIONS: dict[str, list[MeetingInvitation]] = {}
_CHECKINS: dict[str, list[MeetingCheckIn]] = {}
_CONTENTS: dict[str, list[MeetingContent]] = {}
_TRACES: dict[str, list[ComplianceTrace]] = {}
_LOCK = Lock()


def _now_iso() -> str:
    """返回当前 UTC 时间的 ISO 格式字符串。"""
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_id(prefix: str) -> str:
    """生成指定前缀的唯一 ID。

    参数:
        prefix: ID 前缀字符串。

    返回:
        格式为 "{prefix}-{uuid的8位hex}" 的唯一 ID。
    """
    return f"{prefix}-{uuid4().hex[:8]}"


def _trace(meeting_id: str, action: str, detail: str) -> ComplianceTrace:
    """记录一条合规追踪记录。"""
    item = ComplianceTrace(
        id=_new_id("trace"),
        meeting_id=meeting_id,
        action=action,
        detail=detail,
        created_at=_now_iso(),
    )
    _TRACES.setdefault(meeting_id, []).append(item)
    return item


def _get_meeting(meeting_id: str) -> Meeting:
    """根据 ID 获取会议，不存在时抛出 404 异常。"""
    meeting = _MEETINGS.get(meeting_id)
    if not meeting:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return meeting


def list_meetings() -> list[Meeting]:
    """返回所有会议的列表。"""
    return list(_MEETINGS.values())


def create_meeting(body: MeetingCreate) -> Meeting:
    """创建学术会议。"""
    with _LOCK:
        meeting_id = _new_id("meeting")
        meeting = Meeting(
            id=meeting_id,
            title=body.title,
            type=body.type,
            date=body.date,
            duration=body.duration,
            speaker=body.speaker,
            status=MeetingStatus.SCHEDULED,
        )
        _MEETINGS[meeting_id] = meeting
        _trace(meeting_id, "create", f"创建会议：{meeting.title}")
        return meeting


def update_meeting(meeting_id: str, body: MeetingCreate) -> Meeting:
    """更新指定会议的信息。"""
    with _LOCK:
        _get_meeting(meeting_id)
        meeting = Meeting(
            id=meeting_id,
            title=body.title,
            type=body.type,
            date=body.date,
            duration=body.duration,
            speaker=body.speaker,
            status=MeetingStatus.SCHEDULED,
        )
        _MEETINGS[meeting_id] = meeting
        _trace(meeting_id, "update", f"更新会议：{meeting.title}")
        return meeting


def delete_meeting(meeting_id: str) -> dict[str, str]:
    """删除指定会议及其所有关联数据。"""
    with _LOCK:
        _get_meeting(meeting_id)
        _MEETINGS.pop(meeting_id, None)
        _INVITATIONS.pop(meeting_id, None)
        _CHECKINS.pop(meeting_id, None)
        _CONTENTS.pop(meeting_id, None)
        _TRACES.pop(meeting_id, None)
        return {"id": meeting_id, "status": "deleted"}


def invite_hcp(meeting_id: str, body: MeetingInviteCreate) -> MeetingInvitation:
    """邀请 HCP 参与会议。"""
    with _LOCK:
        _get_meeting(meeting_id)
        invitation = MeetingInvitation(
            id=_new_id("invite"),
            meeting_id=meeting_id,
            hcp_id=body.hcp_id,
            status=body.status,
        )
        _INVITATIONS.setdefault(meeting_id, []).append(invitation)
        _trace(meeting_id, "invite", f"邀约HCP：{body.hcp_id}")
        return invitation


def checkin_hcp(meeting_id: str, body: MeetingCheckInCreate) -> MeetingCheckIn:
    """记录 HCP 签到。"""
    with _LOCK:
        _get_meeting(meeting_id)
        checkin = MeetingCheckIn(
            id=_new_id("checkin"),
            meeting_id=meeting_id,
            hcp_id=body.hcp_id,
            checkin_time=body.checkin_time or _now_iso(),
            channel=body.channel,
        )
        _CHECKINS.setdefault(meeting_id, []).append(checkin)
        _trace(meeting_id, "checkin", f"HCP签到：{body.hcp_id}")
        return checkin


def push_content(meeting_id: str, body: MeetingContentCreate) -> MeetingContent:
    """向指定 HCP 推送会议内容。"""
    with _LOCK:
        _get_meeting(meeting_id)
        content = MeetingContent(
            id=_new_id("content"),
            meeting_id=meeting_id,
            title=body.title,
            content_type=body.content_type,
            url=body.url,
            pushed_to=body.hcp_ids,
        )
        _CONTENTS.setdefault(meeting_id, []).append(content)
        _trace(meeting_id, "content_push", f"推送内容：{body.title}")
        return content


def get_effectiveness(meeting_id: str) -> MeetingEffectiveness:
    """获取会议效果评估（签到率、内容推送量、效果评分）。"""
    _get_meeting(meeting_id)
    invited_count = len(_INVITATIONS.get(meeting_id, []))
    checked_in_count = len(_CHECKINS.get(meeting_id, []))
    content_push_count = sum(len(item.pushed_to) or 1 for item in _CONTENTS.get(meeting_id, []))
    attendance_rate = round(checked_in_count / invited_count, 4) if invited_count else 0.0
    effectiveness_score = min(100, int(attendance_rate * 70 + min(content_push_count, 10) * 3))
    return MeetingEffectiveness(
        meeting_id=meeting_id,
        invited_count=invited_count,
        checked_in_count=checked_in_count,
        content_push_count=content_push_count,
        attendance_rate=attendance_rate,
        effectiveness_score=effectiveness_score,
    )


def get_compliance_traces(meeting_id: str) -> list[ComplianceTrace]:
    """获取会议的合规追踪记录列表。"""
    _get_meeting(meeting_id)
    return _TRACES.get(meeting_id, [])
