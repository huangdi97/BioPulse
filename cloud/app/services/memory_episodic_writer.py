"""情景记忆写入与巩固逻辑。"""

import json
from collections.abc import Callable

from cloud.app.repositories import (
    EpisodicMemoryRepository,
    MemoryConsolidationLogRepository,
    MemoryEntriesRepository,
)
from cloud.app.services.memory_format import (
    _call_ai,
    _now,
    build_abstract_prompt,
    build_consolidation_prompt,
    parse_abstract_reply,
    parse_consolidation_reply,
)


class EpisodicMemoryWriter:
    """负责 episodic_memory 写入，以及从情景记忆生成长期记忆条目。"""

    def __init__(self, db, auto_associate: Callable[[int, dict], None]):
        self.db = db
        self._auto_associate = auto_associate

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
