"""数据同步服务模块。"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List

from assistant.app.repositories import SyncQueueRepository
from shared.base_service import BaseService
from shared.columns import (
    TABLE_ASSISTANT_HCP_COLS,
    TABLE_HEALTH_RADAR_COLS,
    TABLE_KNOWLEDGE_BASE_COLS,
    TABLE_SURGERY_REMINDER_COLS,
    TABLE_TASK_COLS,
    TABLE_VISIT_RECORD_COLS,
)

logger = logging.getLogger(__name__)

ENTITY_TABLE_MAP: Dict[str, str] = {
    "hcp": "hcp",
    "visit": "visit_record",
    "task": "task",
    "health_radar": "health_radar",
    "surgery_reminder": "surgery_reminder",
    "knowledge": "knowledge_base",
}

ENTITY_COLUMNS_MAP = {
    "hcp": TABLE_ASSISTANT_HCP_COLS,
    "visit": TABLE_VISIT_RECORD_COLS,
    "task": TABLE_TASK_COLS,
    "health_radar": TABLE_HEALTH_RADAR_COLS,
    "surgery_reminder": TABLE_SURGERY_REMINDER_COLS,
    "knowledge": TABLE_KNOWLEDGE_BASE_COLS,
}

TABLE_ORDER = [
    "hcp",
    "visit_record",
    "task",
    "health_radar",
    "surgery_reminder",
    "knowledge_base",
]

TABLES_WITH_UPDATED_AT = {"hcp", "health_radar", "surgery_reminder", "knowledge_base"}
TABLES_WITH_IS_ACTIVE = {
    "hcp",
    "health_radar",
    "surgery_reminder",
    "knowledge_base",
    "hcp_location",
}


class SyncService(BaseService):
    """数据同步服务，处理客户端数据推送、拉取与冲突检测。"""

    def push(self, body, user_id: int) -> dict:
        """接收客户端推送的同步操作并逐个应用到本地数据库。

        Args:
            body: 包含 client_id 和 operations 的推送请求体; user_id: 用户ID

        Returns:
            dict: 包含 synced、failed、conflict_count、server_operations 的推送结果
        """
        now = datetime.now(timezone.utc).isoformat()
        results = []
        synced_count = 0
        failed_count = 0
        conflict_count = 0
        repo = SyncQueueRepository(self._connection())
        self._init_conflict_table()

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
            if result.get("conflict_id"):
                conflict_count += 1
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
            "conflict_count": conflict_count,
            "server_operations": results,
        }

    def pull(self, since: str) -> dict:
        """拉取自指定时间以来服务端的数据变更。

        Args:
            since: 上次同步时间戳（ISO格式）

        Returns:
            dict: 包含 changes、deleted_ids、server_time 的拉取结果
        """
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
        """获取同步队列状态统计。

        Returns:
            dict: 包含 total、pending、synced、failed、by_entity 的统计信息
        """
        repo = SyncQueueRepository(self._connection())
        total = repo.count()
        pending = repo.count(conditions=["status='pending'"])
        by_entity = self.db.execute("SELECT entity_type, COUNT(*) as cnt FROM sync_queue GROUP BY entity_type").fetchall()
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

    def _init_conflict_table(self) -> None:
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS sync_conflict_log (id INTEGER PRIMARY KEY AUTOINCREMENT, entity_type TEXT NOT NULL, entity_id INTEGER, local_version TEXT, server_version TEXT, conflict_type TEXT DEFAULT 'last_write_wins', resolution TEXT DEFAULT 'pending', resolved_by TEXT, resolved_at TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        self.db.commit()

    def _detect_conflict(self, entity_type, entity_id, local_version, server_version) -> bool:
        try:
            return abs((datetime.fromisoformat(local_version) - datetime.fromisoformat(server_version)).total_seconds()) < 60
        except (ValueError, TypeError):
            return False

    def _log_conflict(self, entity_type, entity_id, local_version, server_version) -> int:
        cursor = self.db.execute(
            "INSERT INTO sync_conflict_log (entity_type, entity_id, local_version, server_version) VALUES (?, ?, ?, ?)",
            (entity_type, entity_id, local_version, server_version),
        )
        self.db.commit()
        return cursor.lastrowid

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
                        return {
                            "operation_id": 0,
                            "status": "failed",
                            "server_entity_id": None,
                        }
                payload_for_insert = {k: v for k, v in op.payload.items() if k not in ("id", "created_at")}
                cols = ", ".join(payload_for_insert.keys())
                vals = ", ".join("?" for _ in payload_for_insert)
                cursor = self.db.execute(
                    f"INSERT INTO {table} ({cols}, created_by, created_at) VALUES ({vals}, ?, ?)",
                    list(payload_for_insert.values()) + [user_id, now],
                )
                return {
                    "operation_id": 0,
                    "status": "synced",
                    "server_entity_id": cursor.lastrowid,
                }

            elif op.action == "update" and op.entity_id:
                if allowed_cols:
                    unknown = [k for k in op.payload if k not in allowed_cols]
                    if unknown:
                        return {
                            "operation_id": 0,
                            "status": "failed",
                            "server_entity_id": None,
                        }
                conflict_id = None
                if table in TABLES_WITH_UPDATED_AT:
                    server_row = self.db.execute(
                        f"SELECT updated_at FROM {table} WHERE id = ?",
                        (op.entity_id,),
                    ).fetchone()
                    if server_row and server_row["updated_at"]:
                        local_version = op.payload.get("updated_at") or getattr(op, "client_created_at", None)
                        if local_version and self._detect_conflict(
                            op.entity_type,
                            op.entity_id,
                            local_version,
                            server_row["updated_at"],
                        ):
                            conflict_id = self._log_conflict(
                                op.entity_type,
                                op.entity_id,
                                local_version,
                                server_row["updated_at"],
                            )
                if table in TABLES_WITH_UPDATED_AT:
                    op.payload["updated_at"] = now
                payload_for_update = {k: v for k, v in op.payload.items() if k != "id"}
                set_clause = ", ".join(f"{k} = ?" for k in payload_for_update)
                self.db.execute(f"UPDATE {table} SET {set_clause} WHERE id = ?", list(payload_for_update.values()) + [op.entity_id])
                result = {"operation_id": 0, "status": "synced", "server_entity_id": op.entity_id}
                if conflict_id:
                    result["conflict_id"] = conflict_id
                return result
            elif op.action == "delete" and op.entity_id:
                self.db.execute(f"UPDATE {table} SET is_active = 0, updated_at = ? WHERE id = ?", (now, op.entity_id))
                return {"operation_id": 0, "status": "synced", "server_entity_id": op.entity_id}
            return {"operation_id": 0, "status": "failed", "server_entity_id": None}
        except Exception:
            logger.exception("同步失败")
            return {"operation_id": 0, "status": "failed", "server_entity_id": None}

    def _collect_table_changes(self, table: str, since: str) -> dict:
        time_col = "updated_at" if table in TABLES_WITH_UPDATED_AT | {"hcp_location"} else "created_at"
        condition = "AND is_active = 1" if table in TABLES_WITH_IS_ACTIVE else ""
        changes = self.db.execute(f"SELECT * FROM {table} WHERE {time_col} > ? {condition}", (since,)).fetchall()
        if table in TABLES_WITH_IS_ACTIVE:
            deleted = self.db.execute(
                f"SELECT id FROM {table} WHERE {time_col} > ? AND is_active = 0",
                (since,),
            ).fetchall()
        else:
            deleted = []
        return {
            "changes": [dict(r) for r in changes],
            "deleted_ids": [r[0] for r in deleted],
        }
