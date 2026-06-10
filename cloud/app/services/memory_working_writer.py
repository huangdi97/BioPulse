"""工作记忆写入逻辑。"""

from datetime import datetime, timedelta

from cloud.app.repositories import WorkingMemoryRepository


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class WorkingMemoryWriter:
    """负责 working_memory 表的写入、清理与 TTL 刷新。"""

    def __init__(self, db):
        self.db = db

    def working_set(
        self,
        session_id: str,
        slot_key: str,
        slot_value: str,
        slot_type: str,
        ttl_seconds: int,
    ) -> dict:
        n = _now()
        expires_at = (datetime.now() + timedelta(seconds=ttl_seconds)).strftime("%Y-%m-%d %H:%M:%S")
        wm = WorkingMemoryRepository(self.db)
        wm.db.execute(
            "INSERT OR REPLACE INTO working_memory "
            "(session_id,slot_key,slot_value,slot_type,ttl_seconds,created_at,expires_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (session_id, slot_key, slot_value, slot_type, ttl_seconds, n, expires_at),
        )
        wm.db.commit()
        return {
            "session_id": session_id,
            "slot_key": slot_key,
            "slot_value": slot_value,
            "expires_at": expires_at,
        }

    def working_clear(self, session_id: str) -> str:
        WorkingMemoryRepository(self.db).db.execute("DELETE FROM working_memory WHERE session_id=?", (session_id,))
        return f"Cleared all slots for session {session_id}"

    def working_refresh(self, session_id: str) -> dict:
        wm = WorkingMemoryRepository(self.db)
        rows = wm.db.execute(
            "SELECT id, ttl_seconds FROM working_memory WHERE session_id=?",
            (session_id,),
        ).fetchall()
        for r in rows:
            ex = (datetime.now() + timedelta(seconds=r["ttl_seconds"])).strftime("%Y-%m-%d %H:%M:%S")
            wm.db.execute("UPDATE working_memory SET expires_at=? WHERE id=?", (ex, r["id"]))
        wm.db.commit()
        return {"session_id": session_id, "refreshed_count": len(rows)}
