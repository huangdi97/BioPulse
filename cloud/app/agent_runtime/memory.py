"""Agent 记忆与脑状态管理模块。"""

import json
from datetime import datetime


class Memory:
    """Agent 短期脑状态存储，支持键值对读写及 JSON/str/int/float 类型。"""

    def __init__(self, agent_db):
        self._agent_db = agent_db

    def get(self, agent_key: str, key: str, user_id: int = 0) -> any:
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

    def set(self, agent_key: str, key: str, value: any, user_id: int = 0):
        if isinstance(value, str):
            value_type = "str"
        elif isinstance(value, (int, float)):
            value_type = "int" if isinstance(value, int) else "float"
            value = str(value)
        else:
            value_type = "json"
            value = json.dumps(value, ensure_ascii=False)

        self._agent_db.execute(
            "INSERT INTO agent_brains (agent_key, user_id, key, value, value_type, updated_at) "
            "VALUES (?, ?, ?, ?, ?, datetime('now')) "
            "ON CONFLICT(agent_key, user_id, key) DO UPDATE SET value=excluded.value, value_type=excluded.value_type, updated_at=excluded.updated_at",
            (agent_key, user_id, key, value, value_type),
        )
        self._agent_db.commit()

    def delete(self, agent_key: str, key: str, user_id: int = 0):
        self._agent_db.execute(
            "DELETE FROM agent_brains WHERE agent_key=? AND user_id=? AND key=?",
            (agent_key, user_id, key),
        )
        self._agent_db.commit()

    def search(self, agent_key: str, keyword: str, limit: int = 5) -> list[dict]:
        rows = self._agent_db.execute(
            "SELECT key, value, value_type FROM agent_brains WHERE agent_key=? AND (key LIKE ? OR value LIKE ?) ORDER BY updated_at DESC LIMIT ?",
            (agent_key, f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]


class AgentMemory:
    """Agent 长期记忆存储，支持按 session 存取及关键词搜索。"""

    def __init__(self, business_db):
        self._business_db = business_db

    def save(self, agent_key: str, session_id: str, entry: dict) -> None:
        self._business_db.execute(
            "INSERT INTO memory_gates (agent_key, session_id, content, created_at) VALUES (?, ?, ?, ?)",
            (agent_key, session_id, json.dumps(entry), datetime.now().isoformat()),
        )
        self._business_db.commit()

    def load(self, agent_key: str, limit: int = 5) -> list[dict]:
        cur = self._business_db.execute(
            "SELECT * FROM memory_gates WHERE agent_key = ? ORDER BY created_at DESC LIMIT ?",
            (agent_key, limit),
        )
        return [dict(r) for r in cur.fetchall()]

    def search(self, agent_key: str, keyword: str, limit: int = 5) -> list[dict]:
        rows = self._business_db.execute(
            "SELECT * FROM memory_gates WHERE agent_key=? AND content LIKE ? ORDER BY created_at DESC LIMIT ?",
            (agent_key, f"%{keyword}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_session(self, agent_key: str, session_id: str) -> dict:
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
