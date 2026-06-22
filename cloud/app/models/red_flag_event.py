"""红灯事件模型 — 合规检查触发的红灯事件结构化定义。"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4


class RedFlagSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RedFlagStatus(str, Enum):
    open = "open"
    investigating = "investigating"
    resolved = "resolved"


@dataclass
class RedFlagEvent:
    """合规红灯事件，由全息校验引擎在发现异常时触发。"""

    red_flag_id: str
    severity: RedFlagSeverity
    rep_id: str
    region: str
    description: str
    evidence_chain: list[str]
    detected_at: str
    status: RedFlagStatus
    assigned_to: Optional[str] = None

    @classmethod
    def create(
        cls,
        severity: RedFlagSeverity,
        rep_id: str,
        region: str,
        description: str,
        evidence_chain: list[str],
        assigned_to: Optional[str] = None,
    ) -> "RedFlagEvent":
        return cls(
            red_flag_id=uuid4().hex[:12],
            severity=severity,
            rep_id=rep_id,
            region=region,
            description=description,
            evidence_chain=evidence_chain,
            detected_at=datetime.now(timezone.utc).isoformat(),
            status=RedFlagStatus.open,
            assigned_to=assigned_to,
        )

    def to_dict(self) -> dict:
        return {
            "red_flag_id": self.red_flag_id,
            "severity": self.severity.value,
            "rep_id": self.rep_id,
            "region": self.region,
            "description": self.description,
            "evidence_chain": self.evidence_chain,
            "detected_at": self.detected_at,
            "status": self.status.value,
            "assigned_to": self.assigned_to,
        }
