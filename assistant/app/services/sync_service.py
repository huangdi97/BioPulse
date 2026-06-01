import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from shared.columns import (
    TABLE_ASSISTANT_HCP_COLS, TABLE_VISIT_RECORD_COLS, TABLE_TASK_COLS,
    TABLE_HEALTH_RADAR_COLS, TABLE_SURGERY_REMINDER_COLS, TABLE_KNOWLEDGE_BASE_COLS,
)
from assistant.app.repositories import SyncQueueRepository
from assistant.app.services.base import BaseService

ENTITY_TABLE_MAP: Dict[str, str] = {
    "hcp": "hcp",
    "visit": "visit_record",
    "task": "task",
    "health_radar": "health_radar",
    "surgery_reminder": "surgery_reminder",
    "knowledge": "knowledge_base",
}

ENTITY_COLUMNS_MAP = {
    'hcp': TABLE_ASSISTANT_HCP_COLS,
    'visit': TABLE_VISIT_RECORD_COLS,
    'task': TABLE_TASK_COLS,
    'health_radar': TABLE_HEALTH_RADAR_COLS,
    'surgery_reminder': TABLE_SURGERY_REMINDER_COLS,
    'knowledge': TABLE_KNOWLEDGE_BASE_COLS,
}

TABLE_ORDER = ["hcp", "visit_record", "task", "health_radar", "surgery_reminder", "knowledge_base"]

TABLES_WITH_UPDATED_AT = {"hcp", "health_radar", "surgery_reminder", "knowledge_base"}
TABLES_WITH_IS_ACTIVE = {'hcp', 'health_radar', 'surgery_reminder', 'knowledge_base', 'hcp_location'}


class SyncService(BaseService):
    def push(self, body, user_id: int) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        results = []
        synced_count = 0
        failed_count = 0
        repo = SyncQueueRepository(self.db)

        for op in body.operations:
            op_id = repo.create(
                data={
                    "client_id": body.client_id,
                    "action": op.action,
                    "entity_type": op.entity_type,
                    "entity_id": op.entity_id,
                    "payload": json.dumps(op.payload, ensure_ascii=False),
                    "status": "pending",
                    "client_created_at": op.client_created_at,
                },
                extra={"created_by": user_id, "created_at": now},
            )

            result = self._apply_operation(op, user_id, now)
            result["operation_id"] = op_id
            if result["status"] == "synced":
                repo.update(op_id, {"status": "synced", "synced_at": now})
                synced_count += 1
            else:
                repo.update(op_id, {"status": "failed"})
                failed_count += 1
            results.append(result)

        return {
            "synced": synced_count,
            "failed": failed_count,
            "server_operations": results,
        }

    def pull(self, since: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        changes: Dict[str, List[dict]] = {}
        deleted_ids: Dict[str, List[int]] = {}

        for table in TABLE_ORDER:
            result = self._collect_table_changes(table, since)
            if result["changes"]:
                changes[table] = result["changes"]
            if result["deleted_ids"]:
                deleted_ids[table] = result["deleted_ids"]

        return {
            "since": since,
            "changes": changes,
            "deleted_ids": deleted_ids,
            "server_time": now,
        }

    def get_status(self) -> dict:
        repo = SyncQueueRepository(self.db)
        total = repo.count()
        pending = repo.count(conditions=["status='pending'"])
        by_entity = self.db.execute(
            "SELECT entity_type, COUNT(*) as cnt FROM sync_queue GROUP BY entity_type"
        ).fetchall()
        by_entity_map = {r["entity_type"]: r["cnt"] for r in by_entity}
        synced = repo.count(conditions=["status='synced'"])
        failed = repo.count(conditions=["status='failed'"])
        return {
            "total": total,
            "pending": pending,
            "synced": synced,
            "failed": failed,
            "by_entity": by_entity_map,
        }

    def _apply_operation(self, op, user_id: int, now: str) -> dict:
        table = ENTITY_TABLE_MAP.get(op.entity_type)
        if not table or op.action not in ("create", "update", "delete"):
            return {"operation_id": 0, "status": "failed", "server_entity_id": None}

        allowed_cols = ENTITY_COLUMNS_MAP.get(op.entity_type)

        try:
            if op.action == "create":
                if allowed_cols:
                    unknown = [k for k in op.payload if k not in allowed_cols]
                    if unknown:
                        return {"operation_id": 0, "status": "failed", "server_entity_id": None}
                payload_for_insert = {k: v for k, v in op.payload.items() if k not in ('id', 'created_at')}
                cols = ", ".join(payload_for_insert.keys())
                vals = ", ".join("?" for _ in payload_for_insert)
                cursor = self.db.execute(
                    f"INSERT INTO {table} ({cols}, created_by, created_at) VALUES ({vals}, ?, ?)",
                    list(payload_for_insert.values()) + [user_id, now],
                )
                return {"operation_id": 0, "status": "synced", "server_entity_id": cursor.lastrowid}

            elif op.action == "update" and op.entity_id:
                if allowed_cols:
                    unknown = [k for k in op.payload if k not in allowed_cols]
                    if unknown:
                        return {"operation_id": 0, "status": "failed", "server_entity_id": None}
                if table in TABLES_WITH_UPDATED_AT:
                    op.payload["updated_at"] = now
                payload_for_update = {k: v for k, v in op.payload.items() if k != 'id'}
                set_clause = ", ".join(f"{k} = ?" for k in payload_for_update)
                self.db.execute(
                    f"UPDATE {table} SET {set_clause} WHERE id = ?",
                    list(payload_for_update.values()) + [op.entity_id],
                )
                return {"operation_id": 0, "status": "synced", "server_entity_id": op.entity_id}

            elif op.action == "delete" and op.entity_id:
                self.db.execute(
                    f"UPDATE {table} SET is_active = 0, updated_at = ? WHERE id = ?",
                    (now, op.entity_id),
                )
                return {"operation_id": 0, "status": "synced", "server_entity_id": op.entity_id}

            return {"operation_id": 0, "status": "failed", "server_entity_id": None}
        except Exception:
            return {"operation_id": 0, "status": "failed", "server_entity_id": None}

    def _collect_table_changes(self, table: str, since: str) -> dict:
        has_updated = table in ("hcp", "health_radar", "surgery_reminder", "knowledge_base", "hcp_location")
        time_col = "updated_at" if has_updated else "created_at"
        condition = 'AND is_active = 1' if table in TABLES_WITH_IS_ACTIVE else ''
        changes = self.db.execute(
            f"SELECT * FROM {table} WHERE {time_col} > ? {condition}", (since,)
        ).fetchall()
        if table in TABLES_WITH_IS_ACTIVE:
            deleted = self.db.execute(
                f"SELECT id FROM {table} WHERE {time_col} > ? AND is_active = 0", (since,)
            ).fetchall()
        else:
            deleted = []
        return {
            "changes": [dict(r) for r in changes],
            "deleted_ids": [r[0] for r in deleted],
        }
