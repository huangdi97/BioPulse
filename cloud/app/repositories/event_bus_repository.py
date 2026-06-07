"""事件总线定义、消息、投递日志等数据访问层。"""

from cloud.shared.repository import BaseRepository
from shared.columns import (
    TABLE_EVENT_BUS_DEFINITIONS_COLS,
    TABLE_EVENT_BUS_MESSAGES_COLS,
    TABLE_EVENT_DELIVERY_LOG_COLS,
)


class EventBusDefinitionsRepository(BaseRepository):
    """事件总线定义表。"""

    def __init__(self, db):
        super().__init__(db, "event_bus_definitions", TABLE_EVENT_BUS_DEFINITIONS_COLS)

    def get_by_event_type(self, event_type: str):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE event_type=?",
            (event_type,),
        ).fetchone()
        return dict(row) if row else None

    def list_filtered(self, source_end=None, enabled=None):
        conditions = ["1=1"]
        params = []
        if source_end:
            conditions.append("source_end=?")
            params.append(source_end)
        if enabled is not None:
            conditions.append("enabled=?")
            params.append(enabled)
        placeholders = ", ".join(self.cols)
        where = " AND ".join(conditions)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE {where} ORDER BY priority ASC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def toggle_enabled(self, event_type: str):
        self.db.execute(
            "UPDATE event_bus_definitions SET enabled = CASE WHEN enabled=1 THEN 0 ELSE 1 END WHERE event_type=?",
            (event_type,),
        )
        self.db.commit()

    def count_all(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]


class EventBusMessagesRepository(BaseRepository):
    """事件总线消息表。"""

    def __init__(self, db):
        super().__init__(db, "event_bus_messages", TABLE_EVENT_BUS_MESSAGES_COLS)

    def get_by_message_id(self, message_id: str):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE message_id=?",
            (message_id,),
        ).fetchone()
        return dict(row) if row else None

    def list_filtered(
        self,
        event_type=None,
        status=None,
        source_end=None,
        start_date=None,
        end_date=None,
    ):
        conditions = ["1=1"]
        params = []
        if event_type:
            conditions.append("event_type=?")
            params.append(event_type)
        if status:
            conditions.append("status=?")
            params.append(status)
        if source_end:
            conditions.append("source_end=?")
            params.append(source_end)
        if start_date:
            conditions.append("created_at >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("created_at <= ?")
            params.append(end_date)
        placeholders = ", ".join(self.cols)
        where = " AND ".join(conditions)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE {where} ORDER BY created_at DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def mark_delivered(self, message_id: str):
        self.db.execute(
            "UPDATE event_bus_messages SET status='delivered', delivered_at=CURRENT_TIMESTAMP WHERE message_id=?",
            (message_id,),
        )
        self.db.commit()

    def mark_pending_with_retry(self, message_id: str):
        self.db.execute(
            "UPDATE event_bus_messages SET status='pending', retry_count=retry_count+1 WHERE message_id=?",
            (message_id,),
        )
        self.db.commit()

    def count_by_status(self):
        return {
            "pending": self.db.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE status='pending'").fetchone()[0],
            "delivered": self.db.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE status='delivered'").fetchone()[0],
            "failed": self.db.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE status='failed'").fetchone()[0],
        }

    def count_all(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]

    def top_event_types(self, limit=5):
        ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT event_type, COUNT(*) as cnt FROM {self.table_name} GROUP BY event_type ORDER BY cnt DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_recent(self, limit=5):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


class EventDeliveryLogRepository(BaseRepository):
    """事件投递日志表。"""

    def __init__(self, db):
        super().__init__(db, "event_delivery_log", TABLE_EVENT_DELIVERY_LOG_COLS)

    def list_filtered(self, message_id=None, target_end=None, delivery_status=None):
        conditions = ["1=1"]
        params = []
        if message_id:
            conditions.append("message_id=?")
            params.append(message_id)
        if target_end:
            conditions.append("target_end=?")
            params.append(target_end)
        if delivery_status:
            conditions.append("delivery_status=?")
            params.append(delivery_status)
        placeholders = ", ".join(self.cols)
        where = " AND ".join(conditions)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE {where} ORDER BY id",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def list_by_message_id(self, message_id: str):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE message_id=? ORDER BY id",
            (message_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def reset_pending_by_message(self, message_id: str):
        self.db.execute(
            "UPDATE event_delivery_log SET delivery_status='pending', error_message='', response_summary='', attempt=attempt+1 WHERE message_id=?",
            (message_id,),
        )
        self.db.commit()

    def count_all(self):
        return self.db.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]

    def count_by_status(self):
        return {
            "delivered": self.db.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE delivery_status='delivered'").fetchone()[0],
            "pending": self.db.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE delivery_status='pending'").fetchone()[0],
        }
