"""程序记忆写入逻辑。"""

import json
from collections.abc import Callable
from datetime import datetime, timedelta

from cloud.app.repositories import MemoryEntriesRepository
from cloud.app.services.memory_format import _now


class ProceduralMemoryWriter:
    """负责程序记忆学习与长期记忆衰减。"""

    def __init__(self, db, auto_associate: Callable[[int, dict], None]):
        self.db = db
        self._auto_associate = auto_associate

    def procedural_learn(
        self,
        pattern_name: str,
        trigger_conditions: str,
        action_sequence: str,
        success_rate: float,
    ) -> dict:
        n = _now()
        content = json.dumps(
            {
                "trigger_conditions": trigger_conditions,
                "action_sequence": action_sequence,
                "success_rate": success_rate,
            },
            ensure_ascii=False,
        )
        eid = MemoryEntriesRepository(self.db).create(
            {
                "title": pattern_name,
                "content": content,
                "memory_type": "procedural",
                "source_type": "procedural_learn",
                "source_id": pattern_name,
                "importance": min(max(float(success_rate), 0.0), 1.0),
                "context_tags": "[]",
                "access_count": 0,
                "created_by": 0,
                "created_at": n,
                "updated_at": n,
            }
        )
        fetched = MemoryEntriesRepository(self.db).get_by_id(eid)
        if fetched:
            self._auto_associate(eid, fetched)
        return {"id": eid, "pattern_name": pattern_name, "success_rate": success_rate}

    def memory_decay(self, hours_threshold: int = 72) -> dict:
        me_repo = MemoryEntriesRepository(self.db)
        cutoff = (datetime.now() - timedelta(hours=hours_threshold)).strftime("%Y-%m-%d %H:%M:%S")
        rows = me_repo.db.execute(
            "SELECT id FROM memory_entries WHERE is_active=1 AND (last_accessed IS NULL OR last_accessed < ?) AND created_at < ?",
            (cutoff, cutoff),
        ).fetchall()
        for r in rows:
            me_repo.db.execute("UPDATE memory_entries SET is_active=0 WHERE id=?", (r["id"],))
        if rows:
            me_repo.db.commit()
        return {"decayed": len(rows), "hours_threshold": hours_threshold}
