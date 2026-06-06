"""离线同步服务模块。"""

import json
import os
from datetime import datetime, timedelta, timezone

import httpx

from assistant.app.services.base import BaseService
from shared.config import settings

CLOUD_API_URL = settings.CLOUD_API_URL
OFFLINE_MODE_VAR = "OFFLINE_MODE"
AI_CACHE_TTL_HOURS = 24

ENTITY_ENDPOINTS = {
    "hcp": "/api/hcp",
    "visit": "/api/visit",
    "task": "/api/task",
    "health_radar": "/api/health-radar",
    "surgery_reminder": "/api/surgery-reminder",
    "knowledge": "/api/knowledge",
}

LOCAL_TABLES = [
    "hcp",
    "visit_record",
    "task",
    "health_radar",
    "surgery_reminder",
    "knowledge_base",
    "hcp_location",
]


class OfflineService(BaseService):
    """Offline 服务类。"""

    def get_status(self) -> dict:
        """获取离线同步状态，包括云端连通性、待同步数量、本地数据摘要。

        Returns:
            dict: 包含 online、pending_sync_count、local_data_summary、last_sync_time 的状态信息
        """
        online = self._check_cloud()
        pending_count = self._count_unsynced()
        local_summary = self._local_data_summary()
        last_sync = self._last_sync_time()
        return {
            "online": online,
            "pending_sync_count": pending_count,
            "local_data_summary": local_summary,
            "last_sync_time": last_sync,
        }

    def sync_pending(self, limit: int = 50) -> dict:
        """将本地待同步的离线操作逐条推送至云端。

        Args:
            limit: 单次最大同步条数

        Returns:
            dict: 包含 synced_count、failed_count、errors 的同步结果
        """
        rows = self.db.execute(
            "SELECT * FROM offline_sync_log WHERE synced = 0 ORDER BY created_at ASC LIMIT ?",
            (limit,),
        ).fetchall()

        synced_count = 0
        failed_count = 0
        errors = []

        for row in rows:
            log_id = row["id"]
            entity_type = row["entity_type"]
            entity_id = row["entity_id"]
            action = row["action"]
            payload = json.loads(row["payload"] or "{}")
            endpoint = ENTITY_ENDPOINTS.get(entity_type)

            if not endpoint:
                errors.append({"id": log_id, "error": f"unknown entity_type: {entity_type}"})
                failed_count += 1
                self._mark_failed(log_id, f"unknown entity_type: {entity_type}")
                continue

            url = f"{CLOUD_API_URL}{endpoint}"
            if action == "update" and entity_id:
                url = f"{url}/{entity_id}"
            elif action == "delete" and entity_id:
                url = f"{url}/{entity_id}"

            method_map = {"create": "POST", "update": "PUT", "delete": "DELETE"}
            method = method_map.get(action, "POST")

            try:
                resp = httpx.request(method, url, json=payload, timeout=10)
                if resp.is_success:
                    self._mark_synced(log_id)
                    synced_count += 1
                else:
                    msg = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    errors.append({"id": log_id, "error": msg})
                    failed_count += 1
                    self._mark_retry(log_id, msg)
            except Exception as e:
                msg = str(e)
                errors.append({"id": log_id, "error": msg})
                failed_count += 1
                self._mark_retry(log_id, msg)

        return {
            "synced_count": synced_count,
            "failed_count": failed_count,
            "errors": errors,
        }

    def queue_change(self, entity_type: str, entity_id: int, action: str, payload: dict) -> dict:
        """将本地变更写入离线同步队列。

        Args:
            entity_type: 实体类型（如 hcp、visit）; entity_id: 实体ID; action: 操作类型（create/update/delete）; payload: 操作负载数据

        Returns:
            dict: 包含 log_id 的入队结果
        """
        cursor = self.db.execute(
            "INSERT INTO offline_sync_log (entity_type, entity_id, action, payload) VALUES (?, ?, ?, ?)",
            (entity_type, entity_id, action, json.dumps(payload, ensure_ascii=False)),
        )
        self.db.commit()
        return {"log_id": cursor.lastrowid}

    def enable_offline_mode(self) -> dict:
        """启用离线模式。

        Returns:
            dict: 包含 mode 和 pending_sync_count 的状态
        """
        os.environ[OFFLINE_MODE_VAR] = "1"
        pending = self._count_unsynced()
        return {"mode": "offline", "pending_sync_count": pending}

    def enable_online_mode(self) -> dict:
        """启用在线模式，自动同步本地待处理项后切换。

        Returns:
            dict: 包含 mode 的状态
        """
        self.sync_pending(limit=500)
        os.environ.pop(OFFLINE_MODE_VAR, None)
        return {"mode": "online"}

    def init_ai_cache_table(self) -> None:
        """初始化离线AI缓存表结构。"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS offline_ai_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE,
                request_hash TEXT,
                response_json TEXT,
                ai_model TEXT,
                created_at TEXT,
                expires_at TEXT,
                access_count INTEGER DEFAULT 0,
                last_accessed_at TEXT
            )
        """)
        self.db.commit()

    def cache_ai_response(self, cache_key, request_hash, response_json, ttl_hours=24) -> int:
        """缓存AI响应到本地。

        Args:
            cache_key: 缓存键; request_hash: 请求哈希; response_json: 响应JSON; ttl_hours: 缓存有效时长（小时）

        Returns:
            int: 影响行数
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=ttl_hours)
        cursor = self.db.execute(
            "INSERT OR REPLACE INTO offline_ai_cache (cache_key, request_hash, response_json, ai_model, created_at, expires_at, access_count, last_accessed_at) VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
            (cache_key, request_hash, json.dumps(response_json, ensure_ascii=False), "", now.isoformat(), expires_at.isoformat(), now.isoformat()),
        )
        self.db.commit()
        return cursor.rowcount

    def get_cached_response(self, cache_key, request_hash) -> dict | None:
        """获取本地缓存的AI响应。

        Args:
            cache_key: 缓存键; request_hash: 请求哈希

        Returns:
            dict | None: 缓存的响应数据，无缓存或已过期时返回 None
        """
        now = datetime.now(timezone.utc).isoformat()
        row = self.db.execute(
            "SELECT * FROM offline_ai_cache WHERE cache_key = ? AND expires_at > ?",
            (cache_key, now),
        ).fetchone()
        if row:
            self.db.execute(
                "UPDATE offline_ai_cache SET access_count = access_count + 1, last_accessed_at = ? WHERE id = ?",
                (now, row["id"]),
            )
            self.db.commit()
            return json.loads(row["response_json"])
        return None

    def clear_expired_cache(self) -> int:
        """清理过期的AI缓存记录。

        Returns:
            int: 删除的缓存记录数
        """
        now = datetime.now(timezone.utc).isoformat()
        cursor = self.db.execute("DELETE FROM offline_ai_cache WHERE expires_at < ?", (now,))
        self.db.commit()
        return cursor.rowcount

    def _check_cloud(self) -> bool:
        try:
            resp = httpx.get(f"{CLOUD_API_URL}/health", timeout=5)
            return resp.is_success
        except Exception:
            return False

    def _count_unsynced(self) -> int:
        row = self.db.execute("SELECT COUNT(*) AS cnt FROM offline_sync_log WHERE synced = 0").fetchone()
        return row["cnt"] if row else 0

    def _local_data_summary(self) -> dict:
        summary = {}
        for table in LOCAL_TABLES:
            try:
                row = self.db.execute(f"SELECT COUNT(*) AS cnt FROM {table}").fetchone()
                summary[table] = row["cnt"] if row else 0
            except Exception:
                summary[table] = 0
        return summary

    def _last_sync_time(self) -> str:
        row = self.db.execute("SELECT MAX(synced_at) AS last FROM offline_sync_log WHERE synced = 1").fetchone()
        return row["last"] or ""

    def _mark_synced(self, log_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.db.execute(
            "UPDATE offline_sync_log SET synced = 1, synced_at = ? WHERE id = ?",
            (now, log_id),
        )
        self.db.commit()

    def _mark_failed(self, log_id: int, msg: str) -> None:
        self.db.execute(
            "UPDATE offline_sync_log SET retry_count = retry_count + 1, error_msg = ? WHERE id = ?",
            (msg, log_id),
        )
        self.db.commit()

    def _mark_retry(self, log_id: int, msg: str) -> None:
        self.db.execute(
            "UPDATE offline_sync_log SET retry_count = retry_count + 1, error_msg = ? WHERE id = ?",
            (msg, log_id),
        )
        self.db.commit()
