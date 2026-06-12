"""RedLightManager — trigger, retrospect, notification, and persistence orchestration."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Optional

from shared.base import AppException, ErrorCode

from .models import (
    LEVEL_TO_ROLE,
    NOTIFY_ROLES,
    NotificationRecord,
    RedLightEvent,
    _now,
)
from .scoring import (
    evidence_score,
    level_from_score,
    level_rank,
    normalize_level,
    should_revoke,
)


class RedLightManager:
    """Manager for red-light trigger, notification, pause, and review flows."""

    def __init__(self, db: Optional[sqlite3.Connection] = None):
        self.db = db
        self._events: dict[str, RedLightEvent] = {}
        self._active_by_agent: dict[str, str] = {}
        self._incentive_pause: dict[str, bool] = {}
        self._sequence = 0
        if self.db:
            self._ensure_tables()

    def trigger(
        self,
        agent_id: str,
        level: str,
        evidence: dict[str, Any],
        notify_levels: Optional[list[str]] = None,
    ) -> RedLightEvent:
        normalized_level = normalize_level(level)
        event_id = self._next_event_id(agent_id)
        now = _now()
        event = RedLightEvent(
            event_id=event_id,
            agent_id=agent_id,
            level=normalized_level,
            evidence=evidence or {},
            status="active",
            incentives_paused=True,
            created_at=now,
            updated_at=now,
            history=[{"action": "trigger", "level": normalized_level, "evidence": evidence or {}, "created_at": now}],
        )
        event.notifications = self._notify(event, notify_levels)
        self._events[event_id] = event
        self._active_by_agent[agent_id] = event_id
        self._incentive_pause[agent_id] = True
        self._persist_event(event)
        return event

    def retrospect(self, agent_id: str, new_evidence: dict[str, Any]) -> Optional[RedLightEvent]:
        active = self.get_active(agent_id)
        if should_revoke(new_evidence):
            return self._revoke(active, new_evidence) if active else None
        score = evidence_score(new_evidence)
        if not active and score >= 0.78:
            return self.trigger(agent_id, level_from_score(score), new_evidence, ["L1", "L2", "L3"])
        if not active:
            return None
        return self._upgrade_or_keep(active, new_evidence, score)

    def get_active(self, agent_id: str) -> Optional[RedLightEvent]:
        event_id = self._active_by_agent.get(agent_id)
        event = self._events.get(event_id or "")
        return event if event and event.status == "active" else None

    def get_notifications(self, agent_id: Optional[str] = None) -> list[NotificationRecord]:
        notifications = [notification for event in self._events.values() for notification in event.notifications]
        if agent_id is None:
            return notifications
        return [notification for notification in notifications if notification.agent_id == agent_id]

    def is_incentive_paused(self, agent_id: str) -> bool:
        return self._incentive_pause.get(agent_id, False)

    def _ensure_tables(self) -> None:
        self.db.execute("""CREATE TABLE IF NOT EXISTS compliance_red_light_events (
            event_id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            level TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            status TEXT NOT NULL,
            incentives_paused INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS compliance_red_light_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            role TEXT NOT NULL,
            role_name TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        self.db.commit()

    def _persist_event(self, event: RedLightEvent) -> None:
        if not self.db:
            return
        with self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO compliance_red_light_events "
                "(event_id, agent_id, level, evidence_json, status, incentives_paused, "
                "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event.event_id,
                    event.agent_id,
                    event.level,
                    json.dumps(event.evidence, ensure_ascii=False),
                    event.status,
                    1 if event.incentives_paused else 0,
                    event.created_at,
                    event.updated_at,
                ),
            )
            for notification in event.notifications:
                self.db.execute(
                    "INSERT INTO compliance_red_light_notifications "
                    "(event_id, agent_id, role, role_name, message, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        notification.event_id,
                        notification.agent_id,
                        notification.role,
                        notification.role_name,
                        notification.message,
                        notification.created_at,
                    ),
                )

    def _notify(self, event: RedLightEvent, notify_levels: Optional[list[str]]) -> list[NotificationRecord]:
        roles = self._roles_from_levels(notify_levels)
        now = _now()
        return [
            NotificationRecord(
                event_id=event.event_id,
                agent_id=event.agent_id,
                role=role,
                role_name=NOTIFY_ROLES[role],
                message=f"红灯事件 {event.event_id} 已触发，等级 {event.level}，请处理。",
                created_at=now,
            )
            for role in roles
        ]

    def _roles_from_levels(self, notify_levels: Optional[list[str]]) -> list[str]:
        levels = notify_levels or ["L1", "L2", "L3"]
        roles = []
        for level in levels:
            role = LEVEL_TO_ROLE.get(str(level).upper(), str(level))
            if role not in NOTIFY_ROLES:
                raise AppException(ErrorCode.VALIDATION_ERROR, f"Unsupported notification level: {level}")
            if role not in roles:
                roles.append(role)
        return roles

    def _normalize_level(self, level: str) -> str:
        return normalize_level(level)

    def _next_event_id(self, agent_id: str) -> str:
        self._sequence += 1
        return f"red-{agent_id}-{self._sequence}"

    def _revoke(self, event: RedLightEvent, evidence: dict[str, Any]) -> RedLightEvent:
        now = _now()
        event.status = "revoked"
        event.incentives_paused = False
        event.updated_at = now
        event.history.append({"action": "revoke", "evidence": evidence, "created_at": now})
        self._active_by_agent.pop(event.agent_id, None)
        self._incentive_pause[event.agent_id] = False
        event.notifications.extend(self._notify(event, ["L1", "L2", "L3"]))
        self._persist_event(event)
        return event

    def _upgrade_or_keep(self, event: RedLightEvent, evidence: dict[str, Any], score: float) -> RedLightEvent:
        now = _now()
        new_level = level_from_score(score)
        action = "keep"
        if level_rank(new_level) > level_rank(event.level):
            event.level = new_level
            action = "upgrade"
            event.notifications.extend(self._notify(event, ["L1", "L2", "L3"]))
        event.evidence = {**event.evidence, "retrospective": evidence}
        event.updated_at = now
        event.history.append({"action": action, "level": event.level, "score": score, "evidence": evidence, "created_at": now})
        self._persist_event(event)
        return event
