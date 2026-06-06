"""事件总线服务，负责事件定义、订阅与消息管理。"""

import json
import uuid
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    EventBusDefinitionsRepository,
    EventBusMessagesRepository,
    EventDeliveryLogRepository,
)
from cloud.app.services.base import BaseService

try:
    import redis
    from redis.exceptions import RedisError, ResponseError
except ImportError:
    redis = None
    RedisError = Exception
    ResponseError = Exception

ALL_ENDS = ["cloud", "sales-coach", "sales-assistant", "assistant", "opportunity"]


def _parse_targets(raw):
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        return parsed if parsed else ALL_ENDS.copy()
    except (json.JSONDecodeError, TypeError):
        return ALL_ENDS.copy()


class EventBusService(BaseService):
    """事件总线服务，管理事件定义、订阅、消息发布与投递。"""

    def create_definition(
        self,
        event_type: str,
        display_name: str,
        description: str,
        source_end: str,
        target_ends: list,
        schema_template: dict,
        priority: int,
    ) -> dict:
        def_repo = EventBusDefinitionsRepository(self.db)
        if def_repo.get_by_event_type(event_type):
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Event type already exists")
        def_repo.create(
            {
                "event_type": event_type,
                "display_name": display_name,
                "description": description,
                "source_end": source_end,
                "target_ends": json.dumps(target_ends, ensure_ascii=False),
                "schema_template": json.dumps(schema_template, ensure_ascii=False),
                "priority": priority,
            }
        )
        return def_repo.get_by_event_type(event_type)

    def list_definitions(self, source_end: Optional[str] = None, enabled: Optional[int] = None) -> list:
        return EventBusDefinitionsRepository(self.db).list_filtered(source_end=source_end, enabled=enabled)

    def toggle_definition(self, event_type: str) -> dict:
        def_repo = EventBusDefinitionsRepository(self.db)
        if not def_repo.get_by_event_type(event_type):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Event definition not found")
        def_repo.toggle_enabled(event_type)
        return def_repo.get_by_event_type(event_type)

    def publish_message(
        self,
        event_type: str,
        source_entity_type: str,
        source_entity_id: str,
        payload: dict,
        correlation_id: str,
    ) -> dict:
        def_repo = EventBusDefinitionsRepository(self.db)
        definition = def_repo.get_by_event_type(event_type)
        if not definition or not definition.get("enabled"):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Event type not found or disabled")
        msg_repo = EventBusMessagesRepository(self.db)
        delivery_repo = EventDeliveryLogRepository(self.db)
        message_id = f"evt:{uuid.uuid4()}"
        targets = _parse_targets(definition["target_ends"])
        msg_repo.create(
            {
                "message_id": message_id,
                "event_type": event_type,
                "source_end": definition["source_end"],
                "source_entity_type": source_entity_type,
                "source_entity_id": source_entity_id,
                "payload": json.dumps(payload, ensure_ascii=False),
                "correlation_id": correlation_id,
                "priority": definition["priority"],
            }
        )
        results = []
        for i, target in enumerate(targets):
            is_delivered = i == 0
            status_val = "delivered" if is_delivered else "pending"
            resp = "OK: 200 (simulated)" if is_delivered else ""
            err = "" if is_delivered else f"simulated pending for {target}"
            dur = 25 if is_delivered else 0
            delivery_repo.create(
                {
                    "message_id": message_id,
                    "target_end": target,
                    "delivery_status": status_val,
                    "attempt": 1,
                    "response_summary": resp,
                    "duration_ms": dur,
                    "error_message": err,
                }
            )
            results.append(
                {
                    "target_end": target,
                    "delivery_status": status_val,
                    "error_message": err,
                }
            )
        msg_repo.mark_delivered(message_id)
        return {
            "message": msg_repo.get_by_message_id(message_id),
            "delivery_results": results,
        }

    def list_messages(
        self,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        source_end: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list:
        return EventBusMessagesRepository(self.db).list_filtered(
            event_type=event_type,
            status=status,
            source_end=source_end,
            start_date=start_date,
            end_date=end_date,
        )

    def get_message(self, message_id: str) -> dict:
        msg_repo = EventBusMessagesRepository(self.db)
        msg = msg_repo.get_by_message_id(message_id)
        if not msg:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Message not found")
        logs = EventDeliveryLogRepository(self.db).list_by_message_id(message_id)
        return {"message": msg, "delivery_logs": logs}

    def redeliver_message(self, message_id: str) -> dict:
        msg_repo = EventBusMessagesRepository(self.db)
        if not msg_repo.get_by_message_id(message_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Message not found")
        msg_repo.mark_pending_with_retry(message_id)
        EventDeliveryLogRepository(self.db).reset_pending_by_message(message_id)
        return msg_repo.get_by_message_id(message_id)

    def subscribe(self, target_end: str, event_types: list, callback_url: str = "") -> dict:
        return {
            "acknowledged": True,
            "target_end": target_end,
            "event_types": event_types,
            "callback_url": callback_url,
        }

    def list_delivery_log(
        self,
        message_id: Optional[str] = None,
        target_end: Optional[str] = None,
        delivery_status: Optional[str] = None,
    ) -> list:
        return EventDeliveryLogRepository(self.db).list_filtered(
            message_id=message_id,
            target_end=target_end,
            delivery_status=delivery_status,
        )

    def get_dashboard(self) -> dict:
        def_repo = EventBusDefinitionsRepository(self.db)
        msg_repo = EventBusMessagesRepository(self.db)
        delivery_repo = EventDeliveryLogRepository(self.db)
        msg_counts = msg_repo.count_by_status()
        delivery_counts = delivery_repo.count_by_status()
        overview = {
            "total_definitions": def_repo.count_all(),
            "total_messages": msg_repo.count_all(),
            "pending": msg_counts["pending"],
            "delivered": msg_counts["delivered"],
            "failed": msg_counts["failed"],
            "total_delivery_logs": delivery_repo.count_all(),
            "delivered_logs": delivery_counts["delivered"],
            "pending_logs": delivery_counts["pending"],
        }
        top_types = msg_repo.top_event_types(5)
        recent = msg_repo.list_recent(5)
        return {
            "overview": overview,
            "top_event_types": top_types,
            "recent_messages": recent,
        }


class RedisEventBus:
    """Redis Streams 事件总线，自动降级到 SQLite EventBusService。"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self._available = False
        self._pool = None
        self._client = None
        if redis is None:
            return
        try:
            self._pool = redis.ConnectionPool.from_url(redis_url, max_connections=10)
            self._client = redis.Redis(connection_pool=self._pool)
            self._client.ping()
            self._available = True
        except (RedisError, OSError, ValueError):
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def publish(self, stream: str, event: dict) -> Optional[str]:
        if not self._available or not self._client:
            return None
        try:
            fields = {}
            for k, v in event.items():
                fields[k] = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
            return self._client.xadd(stream, fields, id="*")
        except RedisError:
            return None

    def subscribe(self, stream: str, group: str, consumer: str, timeout_ms: int = 5000) -> list:
        if not self._available or not self._client:
            return []
        try:
            try:
                self._client.xgroup_create(stream, group, id="0", mkstream=True)
            except ResponseError as exc:
                if "BUSYGROUP" not in str(exc):
                    raise
            resp = self._client.xreadgroup(group, consumer, {stream: ">"}, count=10, block=timeout_ms)
            if not resp:
                return []
            result = []
            for _stream_name, messages in resp:
                for msg_id, fields in messages:
                    entry = {"id": msg_id}
                    for k, v in fields.items():
                        try:
                            entry[k] = json.loads(v)
                        except (json.JSONDecodeError, TypeError):
                            entry[k] = v
                    result.append(entry)
            return result
        except RedisError:
            return []

    def ack(self, stream: str, group: str, message_id: str) -> Optional[int]:
        if not self._available or not self._client:
            return None
        try:
            return self._client.xack(stream, group, message_id)
        except RedisError:
            return None

    def pending(self, stream: str, group: str) -> list:
        if not self._available or not self._client:
            return []
        try:
            resp = self._client.xpending(stream, group)
            if not resp:
                return []
            total = resp.get("pending", 0) if isinstance(resp, dict) else resp
            return [{"stream": stream, "group": group, "pending": total}]
        except RedisError:
            return []
