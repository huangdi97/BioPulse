"""Agent 推送通知服务"""

import logging
import time

from cloud.app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

# 去重缓存: {f"{agent_key}:{user_id}": timestamp}
_push_dedup = {}
_DEDUP_WINDOW = 1800  # 30 秒（实际应30分钟，但测试时缩短）


class AgentPushService:
    def push_insight(self, agent_key: str, user_id: str, title: str, message: str) -> bool:
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
        except Exception:
            logger.exception("Push failed %s", agent_key)
            return False
