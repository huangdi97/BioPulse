"""记忆写入服务，负责工作记忆、情景记忆与语义记忆的写入。"""

import json
from datetime import datetime, timedelta

from cloud.app.repositories import (
    EpisodicMemoryRepository,
    MemoryConsolidationLogRepository,
    MemoryEntriesRepository,
    WorkingMemoryRepository,
)
from cloud.app.services.base import BaseService
from cloud.app.services.holographic_service import HolographicService
from cloud.app.services.memory_format import (
    _call_ai,
    _now,
    build_abstract_prompt,
    build_consolidation_prompt,
    parse_abstract_reply,
    parse_consolidation_reply,
)


class MemoryWriter(BaseService):
    """记忆写入服务，提供工作记忆设置、情景记忆记录与语义记忆存储功能。"""

    def __init__(self, db):
        super().__init__(db)

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

    def episodic_store(
        self,
        event_type: str,
        title: str,
        description: str,
        context: dict,
        outcome: str,
        valence: float,
        intensity: float,
        involved_agents: list[str],
        related_entity_type: str,
        related_entity_id: int | None,
        uid: str,
    ) -> dict:
        n = _now()
        em = EpisodicMemoryRepository(self.db)
        new_id = em.create(
            {
                "event_type": event_type,
                "title": title,
                "description": description,
                "context": json.dumps(context, ensure_ascii=False),
                "outcome": outcome,
                "valence": valence,
                "intensity": intensity,
                "involved_agents": json.dumps(involved_agents, ensure_ascii=False),
                "related_entity_type": related_entity_type,
                "related_entity_id": related_entity_id,
                "created_by": uid,
                "created_at": n,
            }
        )
        interference = 0
        if related_entity_id or event_type:
            conds, p = [], []
            if related_entity_id and related_entity_type:
                conds.append("related_entity_id=? AND related_entity_type=?")
                p += [related_entity_id, related_entity_type]
            if event_type:
                conds.append("event_type=?")
                p.append(event_type)
            for old in em.db.execute(
                f"SELECT valence FROM episodic_memory WHERE id!=? AND ({' OR '.join(conds)})",
                [new_id] + p,
            ):
                if (old["valence"] or 0.0) * (valence or 0.0) < 0:
                    interference += 1
        if interference:
            MemoryConsolidationLogRepository(self.db).create(
                {
                    "consolidation_type": "interference_forgetting",
                    "source_table": "episodic_memory",
                    "item_count": interference,
                    "items_superseded": interference,
                    "status": "completed",
                    "details": json.dumps({"new_id": new_id, "triggered_by": uid}, ensure_ascii=False),
                    "created_at": n,
                }
            )
        return {
            "id": new_id,
            "event_type": event_type,
            "title": title,
            "description": description,
            "outcome": outcome,
            "valence": valence,
            "intensity": intensity,
            "involved_agents": involved_agents,
            "related_entity_type": related_entity_type,
            "related_entity_id": related_entity_id,
        }

    def episodic_consolidate(self, memory_id: int, auth_header: str) -> dict:
        em_repo = EpisodicMemoryRepository(self.db)
        me_repo = MemoryEntriesRepository(self.db)
        row = em_repo.get_by_id(memory_id)
        if not row:
            from fastapi import HTTPException
            from starlette import status

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Episodic memory not found")
        if row["is_consolidated"]:
            from fastapi import HTTPException
            from starlette import status

            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already consolidated")
        messages = build_consolidation_prompt(row)
        ai_result = _call_ai(messages, auth_header)
        reply = ai_result.get("reply", "")
        insight = parse_consolidation_reply(reply, row)
        title = insight.get("title", row["title"])
        content = insight.get("content", row["description"])
        memory_type = insight.get("memory_type", "insight")
        importance = float(insight.get("importance", 0.5))
        context_tags = insight.get("context_tags", [])
        if not isinstance(context_tags, list):
            context_tags = []
        now_val = _now()
        entry_id = me_repo.create(
            {
                "title": title,
                "content": content,
                "memory_type": memory_type,
                "source_type": "episodic_consolidation",
                "source_id": f"ep_{memory_id}",
                "importance": min(max(importance, 0.0), 1.0),
                "context_tags": json.dumps(context_tags, ensure_ascii=False),
                "access_count": 0,
                "created_by": 1,
                "created_at": now_val,
                "updated_at": now_val,
            }
        )
        em_repo.update(memory_id, {"is_consolidated": 1})
        fetched = me_repo.get_by_id(entry_id)
        if fetched:
            self._auto_associate(entry_id, fetched)
        return {
            "memory_id": memory_id,
            "entry_id": entry_id,
            "title": title,
            "memory_type": memory_type,
            "importance": importance,
        }

    def semantic_abstract(
        self,
        source_type: str,
        source_id: str,
        abstraction_level: str,
        auth_header: str = "",
    ) -> dict:
        rows = (
            EpisodicMemoryRepository(self.db)
            .db.execute(
                "SELECT * FROM episodic_memory WHERE related_entity_type=? AND related_entity_id=? ORDER BY created_at DESC",
                (source_type, int(source_id)),
            )
            .fetchall()
        )
        if not rows:
            from fastapi import HTTPException
            from starlette import status

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Episodic memories for abstraction not found")
        txt = "\n".join(f"{r['title']}: {r['description']}" for r in rows)
        msg = build_abstract_prompt(rows, abstraction_level, txt)
        reply = _call_ai(msg, auth_header).get("reply", "")
        d = parse_abstract_reply(reply, source_type, txt[:200])
        n = _now()
        eid = MemoryEntriesRepository(self.db).create(
            {
                "title": d.get("title", ""),
                "content": d.get("content", txt[:200]),
                "memory_type": "semantic",
                "source_type": source_type,
                "source_id": str(source_id),
                "importance": 0.7,
                "context_tags": json.dumps(d.get("context_tags", []), ensure_ascii=False),
                "access_count": 0,
                "created_by": 0,
                "created_at": n,
                "updated_at": n,
            }
        )
        fetched = MemoryEntriesRepository(self.db).get_by_id(eid)
        if fetched:
            self._auto_associate(eid, fetched)
        return {"id": eid, "title": d.get("title", ""), "content": d.get("content", "")}

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

    def _auto_associate(self, entry_id: int, entry: dict):
        HolographicService(self.db).auto_associate(entry_id, entry)
