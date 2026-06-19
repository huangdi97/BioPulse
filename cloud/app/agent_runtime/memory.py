"""Agent 记忆与脑状态管理模块。"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any


class Memory:
    """Agent 短期脑状态存储，支持键值对读写及 JSON/str/int/float 类型。"""

    _agent_db: sqlite3.Connection

    def __init__(self, agent_db: sqlite3.Connection) -> None:
        self._agent_db = agent_db

    def get(self, agent_key: str, key: str, user_id: int = 0) -> Any | None:
        """获取 Agent 短期记忆值。"""
        row = self._agent_db.execute(
            "SELECT value, value_type FROM agent_brains WHERE agent_key=? AND user_id=? AND key=?",
            (agent_key, user_id, key),
        ).fetchone()
        if not row:
            return None
        if row["value_type"] == "json":
            return json.loads(row["value"])
        if row["value_type"] == "int":
            return int(row["value"])
        if row["value_type"] == "float":
            return float(row["value"])
        return row["value"]

    def set(self, agent_key: str, key: str, value: Any, user_id: int = 0, importance: float = 0.5) -> None:
        """设置 Agent 短期记忆值。importance（0-1）用于后续淘汰策略。"""
        if isinstance(value, str):
            value_type = "str"
        elif isinstance(value, (int, float)):
            value_type = "int" if isinstance(value, int) else "float"
            value = str(value)
        else:
            value_type = "json"
            value = json.dumps(value, ensure_ascii=False)

        self._agent_db.execute(
            "INSERT INTO agent_brains (agent_key, user_id, key, value, value_type, updated_at, importance) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'), ?) "
            "ON CONFLICT(agent_key, user_id, key) DO UPDATE SET value=excluded.value, "
            "value_type=excluded.value_type, updated_at=excluded.updated_at, importance=excluded.importance",
            (agent_key, user_id, key, value, value_type, importance),
        )
        self._agent_db.commit()

    def delete(self, agent_key: str, key: str, user_id: int = 0) -> None:
        """删除 Agent 短期记忆值。"""
        self._agent_db.execute(
            "DELETE FROM agent_brains WHERE agent_key=? AND user_id=? AND key=?",
            (agent_key, user_id, key),
        )
        self._agent_db.commit()

    def search(self, agent_key: str, keyword: str, limit: int = 5) -> list[dict[str, Any]]:
        """搜索 Agent 短期记忆。"""
        rows = self._agent_db.execute(
            "SELECT key, value, value_type FROM agent_brains WHERE agent_key=? AND (key LIKE ? OR value LIKE ?) ORDER BY updated_at DESC LIMIT ?",
            (agent_key, f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]


# --- 记忆压缩 & 淘汰 ---

def compress_messages(messages: list[dict], max_tokens: int = 4000) -> list[dict]:
    """压缩消息列表。"""
    if not messages:
        return messages
    total_chars = sum(len(m.get("content", "") or "") for m in messages)
    total_tokens = total_chars // 4
    if total_tokens <= max_tokens:
        return messages
    system_msgs = [m for m in messages if m.get("role") == "system"]
    non_system = [m for m in messages if m.get("role") != "system"]
    keep = non_system[-4:] if len(non_system) >= 4 else non_system
    mid = non_system[:-4] if len(non_system) >= 4 else []
    if mid:
        summary_text = " ".join(m.get("content", "")[:100] for m in mid if m.get("content"))
        summary = {"role": "system", "content": f"[记忆摘要：{summary_text[:200]}...]"}
        result = system_msgs + [summary] + keep
    else:
        result = system_msgs + keep
    return result


def evict_old_entries(db, agent_key: str | None = None, ttl_hours: int = 168) -> int:
    """删除超过 ttl_hours 的记忆条目。"""
    import time
    cutoff = time.time() - ttl_hours * 3600
    if agent_key:
        cur = db.execute("DELETE FROM agent_brains WHERE agent_key=? AND updated_at < ?",
                         (agent_key, cutoff))
    else:
        cur = db.execute("DELETE FROM agent_brains WHERE updated_at < ?", (cutoff,))
    db.commit()
    return cur.rowcount


def evict_low_importance(db, threshold: float = 0.2, agent_key: str | None = None) -> int:
    """删除重要性低于 threshold 的记忆条目。"""
    if agent_key:
        cur = db.execute("DELETE FROM agent_brains WHERE agent_key=? AND importance < ?",
                         (agent_key, threshold))
    else:
        cur = db.execute("DELETE FROM agent_brains WHERE importance < ?", (threshold,))
    db.commit()
    return cur.rowcount


def scheduled_maintenance(db, ttl_hours: int = 168, importance_threshold: float = 0.2) -> dict:
    """执行全部维护任务。"""
    old = evict_old_entries(db, ttl_hours=ttl_hours)
    low = evict_low_importance(db, threshold=importance_threshold)
    return {"evicted_old": old, "evicted_low_importance": low, "total": old + low}


class AgentMemory:
    """Agent 长期记忆存储，支持按 session 存取及关键词搜索。"""

    _business_db: sqlite3.Connection

    def __init__(self, business_db: sqlite3.Connection) -> None:
        self._business_db = business_db

    def save(self, agent_key: str, session_id: str, entry: dict[str, Any]) -> None:
        """保存 Agent 长期记忆条目。"""
        self._business_db.execute(
            "INSERT INTO memory_gates (agent_key, session_id, content, created_at) VALUES (?, ?, ?, ?)",
            (agent_key, session_id, json.dumps(entry), datetime.now().isoformat()),
        )
        self._business_db.commit()

    def load(self, agent_key: str, limit: int = 5) -> list[dict[str, Any]]:
        """加载 Agent 长期记忆。"""
        cur = self._business_db.execute(
            "SELECT * FROM memory_gates WHERE agent_key = ? ORDER BY created_at DESC LIMIT ?",
            (agent_key, limit),
        )
        return [dict(r) for r in cur.fetchall()]

    def search(self, agent_key: str, keyword: str, limit: int = 5) -> list[dict[str, Any]]:
        """搜索 Agent 长期记忆。"""
        rows = self._business_db.execute(
            "SELECT * FROM memory_gates WHERE agent_key=? AND content LIKE ? ORDER BY created_at DESC LIMIT ?",
            (agent_key, f"%{keyword}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_session(self, agent_key: str, session_id: str) -> dict[str, Any]:
        """获取指定 session 的全部记忆条目。"""
        cur = self._business_db.execute(
            "SELECT * FROM memory_gates WHERE agent_key = ? AND session_id = ? ORDER BY created_at",
            (agent_key, session_id),
        )
        rows = cur.fetchall()
        return {
            "agent_key": agent_key,
            "session_id": session_id,
            "entries": [dict(r) for r in rows],
        }


AgentBrain = Memory
