"""Agent 通知模块 — 支持多通道通知与审批请求。"""

import json
import logging
import sqlite3
import threading
import urllib.error
import urllib.request
from datetime import datetime

from shared.ai_gateway import INTERNAL_API_TIMEOUT

logger = logging.getLogger(__name__)


class NotificationChannel:
    EMAIL = "email"
    WEBHOOK = "webhook"
    IN_APP = "in_app"
    TEAMS = "teams"


class Notifier:
    """Agent 通知器，支持 IN_APP / WEBHOOK 多通道通知和审批请求。"""

    def __init__(self, agent_db=None):
        self._agent_db = agent_db
        self._channels: dict[str, callable] = {}

    def register_channel(self, name: str, handler: callable) -> None:
        """注册通知通道处理器。"""
        self._channels[name] = handler

    def notify(self, agent_key: str, goal: str, status: str, elapsed_seconds: float, cost: dict) -> None:
        """发送 Agent 执行完成通知。"""
        message = f"[Agent] {agent_key} | {status} | 耗时:{elapsed_seconds:.1f}s | Token:{cost.get('total_tokens', 0)}"
        logger.info(message)
        self.send(message, priority="normal", channels=[NotificationChannel.IN_APP])

    def send(self, message: str, priority: str = "normal", channels: list[str] | None = None) -> None:
        """发送消息到指定通道。"""
        channels = channels or [NotificationChannel.IN_APP]
        for channel in channels:
            handler = self._channels.get(channel)
            if handler:
                threading.Thread(target=handler, args=(message, priority), daemon=True).start()
            elif channel == NotificationChannel.IN_APP and self._agent_db:
                self._send_in_app(message, priority)
            elif channel == NotificationChannel.WEBHOOK:
                logger.warning("WEBHOOK channel not configured for message: %s", message[:100])

    def send_approval_request(self, agent_name: str, action: str, detail: dict) -> str:
        """发送审批请求。"""
        if not self._agent_db:
            logger.warning("Cannot send approval: no database connection")
            return ""
        request_id = self._create_approval(agent_name, action, detail)
        self.send(f"审批请求: {agent_name} - {action}", priority="high", channels=[NotificationChannel.IN_APP])
        return request_id

    def _send_in_app(self, message: str, priority: str = "normal") -> None:
        if not self._agent_db:
            return
        try:
            self._agent_db.execute(
                "INSERT INTO agent_runtime_logs (agent_key, goal, status, log_detail) VALUES (?, ?, ?, ?)",
                ("_system", message, "notification", json.dumps({"priority": priority, "message": message}, ensure_ascii=False)),
            )
            self._agent_db.commit()
        except sqlite3.Error:
            logger.exception("Failed to send in-app notification")

    def _send_webhook(self, url: str, message: str, priority: str = "normal") -> None:
        body = json.dumps({"text": message, "priority": priority}).encode("utf-8")
        try:
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=INTERNAL_API_TIMEOUT):
                pass
        except (urllib.error.URLError, TimeoutError):
            logger.exception("Failed to send webhook notification to %s", url)

    def _create_approval(self, agent_name: str, action: str, detail: dict) -> str:
        import uuid

        request_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        self._agent_db.execute(
            "INSERT INTO agent_runtime_approvals (trace_id, agent_key, goal, step, tool, params, reasoning, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (request_id, agent_name, action, 0, action, json.dumps(detail, ensure_ascii=False), "", "pending", now),
        )
        self._agent_db.commit()
        return request_id

    def check_approval_status(self, request_id: str) -> str | None:
        """检查审批请求状态。"""
        if not self._agent_db:
            return None
        row = self._agent_db.execute("SELECT status FROM agent_runtime_approvals WHERE trace_id=?", (request_id,)).fetchone()
        return row["status"] if row else None

    def set_webhook_channel(self, name: str, url: str) -> None:
        """设置 Webhook 通知通道。"""
        self._channels[name] = lambda msg, priority=None: self._send_webhook(url, msg, priority or "normal")


AgentNotifier = Notifier
