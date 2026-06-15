"""Agent 推送通知服务"""

import json
import logging
import time
from enum import Enum
from typing import Optional

import httpx

from cloud.app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

# 去重缓存: {f"{agent_key}:{user_id}": timestamp}
_push_dedup = {}
_DEDUP_WINDOW = 1800  # 30 秒（实际应30分钟，但测试时缩短）


class PushEventType(str, Enum):
    COMPLIANCE_RED_LIGHT = "compliance_red_light"
    HIGH_VALUE_SUGGESTION = "high_value_suggestion"
    ANOMALY_DATA = "anomaly_data"


class PushEventFilter:
    """推送事件过滤器——仅允许重要事件类型触发推送。"""

    ALLOWED_EVENT_TYPES = {
        PushEventType.COMPLIANCE_RED_LIGHT,
        PushEventType.HIGH_VALUE_SUGGESTION,
        PushEventType.ANOMALY_DATA,
    }

    @classmethod
    def is_allowed(cls, event_type: str) -> bool:
        return event_type in cls.ALLOWED_EVENT_TYPES

    @classmethod
    def filter_events(cls, events: list[dict]) -> list[dict]:
        return [e for e in events if cls.is_allowed(e.get("event_type", ""))]


class AgentPushService:
    def push_insight(
        self,
        agent_key: str,
        user_id: str,
        title: str,
        message: str,
        event_type: Optional[str] = None,
    ) -> bool:
        if event_type and not PushEventFilter.is_allowed(event_type):
            logger.info("Skipped %s (event_type=%s filtered)", agent_key, event_type)
            return False
        dedup_key = f"{agent_key}:{user_id}"
        now = time.time()
        last = _push_dedup.get(dedup_key)
        if last and (now - last) < _DEDUP_WINDOW:
            logger.info("Dupe: %s within dedup window", dedup_key)
            return False
        _push_dedup[dedup_key] = now
        try:
            svc = NotificationService()
            svc.create_notification(user_id=user_id, title=title, body=message, source="agent")
            logger.info("Pushed %s → %s", agent_key, user_id)
            return True
        except (httpx.HTTPError, json.JSONDecodeError):
            logger.exception("Push failed %s", agent_key)
            return False
