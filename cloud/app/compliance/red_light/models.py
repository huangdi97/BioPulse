"""Data models for red-light events and notifications."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


NOTIFY_ROLES = {
    "compliance_officer": "合规官",
    "regional_manager": "区域经理",
    "president": "总裁",
}

LEVEL_TO_ROLE = {
    "L1": "compliance_officer",
    "L2": "regional_manager",
    "L3": "president",
}


@dataclass
class NotificationRecord:
    """Notification emitted for a red-light event."""

    event_id: str
    agent_id: str
    role: str
    role_name: str
    message: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RedLightEvent:
    """Red-light event with evidence, status, and notification state."""

    event_id: str
    agent_id: str
    level: str
    evidence: dict[str, Any]
    status: str
    incentives_paused: bool
    created_at: str
    updated_at: str
    notifications: list[NotificationRecord] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["notifications"] = [notification.to_dict() for notification in self.notifications]
        return data


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
