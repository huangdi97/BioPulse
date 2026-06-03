import json
import urllib.request
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    EpisodicMemoryRepository,
    MemoryConsolidationLogRepository,
    MemoryEntriesRepository,
    WorkingMemoryRepository,
)
from cloud.app.services.base import BaseService


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _n404(name: str = "Resource") -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{name} not found")


def _call_ai(messages: list[dict], auth_header: str) -> dict:
    payload = {"messages": messages, "temperature": 0.3, "max_tokens": 2048}
    req = urllib.request.Request(
        "http://localhost:8000/ai/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": auth_header},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as rp:
        return json.loads(rp.read().decode("utf-8")).get("data", {})


class BrainMemoryService(BaseService):
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

    def working_get(self, session_id: str, slot_key: Optional[str] = None) -> dict:
        wm = WorkingMemoryRepository(self.db)
        if slot_key:
            row = wm.db.execute(
                "SELECT * FROM working_memory WHERE session_id=? AND slot_key=? AND expires_at>?",
                (session_id, slot_key, _now()),
            ).fetchone()
            if not row:
                raise _n404("Slot")
            return {"data": dict(row)}
        rows = wm.db.execute(
            "SELECT * FROM working_memory WHERE session_id=? AND expires_at>?",
            (session_id, _now()),
        ).fetchall()
        return {"data": [dict(r) for r in rows]}

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
        related_entity_id: Optional[int],
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

    def episodic_list(
        self,
        event_type: Optional[str] = None,
        outcome: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        c, p = ["1=1"], []
        if event_type:
            c.append("event_type=?")
            p.append(event_type)
        if outcome:
            c.append("outcome=?")
            p.append(outcome)
        if date_from:
            c.append("created_at>=?")
            p.append(date_from)
        if date_to:
            c.append("created_at<=?")
            p.append(date_to)
        total, pages, items = EpisodicMemoryRepository(self.db).paginate(
            page=page,
            page_size=page_size,
            conditions=c,
            params=p,
            order_by="created_at DESC",
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": pages,
        }

    def episodic_detail(self, memory_id: int) -> dict:
        em_repo = EpisodicMemoryRepository(self.db)
        row = em_repo.get_by_id(memory_id)
        if not row:
            raise _n404("Episodic memory")
        MemoryConsolidationLogRepository(self.db).create(
            {
                "consolidation_type": "retrieval_reconsolidation",
                "source_table": "episodic_memory",
                "item_count": 1,
                "status": "completed",
                "details": json.dumps({"memory_id": memory_id}, ensure_ascii=False),
                "created_at": _now(),
            }
        )
        return row

    def episodic_consolidate(self, memory_id: int, auth_header: str) -> dict:
        em_repo = EpisodicMemoryRepository(self.db)
        me_repo = MemoryEntriesRepository(self.db)
        row = em_repo.get_by_id(memory_id)
        if not row:
            raise _n404("Episodic memory")
        if row["is_consolidated"]:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already consolidated")
        messages = [
            {
                "role": "system",
                "content": "你是一名记忆巩固专家。请根据输入的情景记忆内容，提炼核心洞察，生成结构化的记忆条目。"
                '输出纯JSON（不要markdown代码块）：{"title":"洞察标题","content":"详细内容","memory_type":"insight",'
                '"importance":0.8,"context_tags":["标签1","标签2"]}',
            },
            {
                "role": "user",
                "content": f"事件类型: {row['event_type']}\n标题: {row['title']}\n"
                f"描述: {row['description']}\n情景: {row['context']}\n结果: {row['outcome']}\n"
                f"情感值: {row['valence']}\n强度: {row['intensity']}",
            },
        ]
        ai_result = _call_ai(messages, auth_header)
        reply = ai_result.get("reply", "")
        try:
            insight = json.loads(reply)
        except (json.JSONDecodeError, TypeError):
            insight = {
                "title": row["title"],
                "content": reply or row["description"],
                "memory_type": "insight",
                "importance": 0.5,
                "context_tags": [],
            }
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
        return {
            "memory_id": memory_id,
            "entry_id": entry_id,
            "title": title,
            "memory_type": memory_type,
            "importance": importance,
        }

    def dashboard(self) -> dict:
        now_val = _now()
        wm_repo = WorkingMemoryRepository(self.db)
        em_repo = EpisodicMemoryRepository(self.db)
        active_sessions = wm_repo.db.execute(
            "SELECT COUNT(DISTINCT session_id) FROM working_memory WHERE expires_at > ?",
            (now_val,),
        ).fetchone()[0]
        slot_total = wm_repo.db.execute(
            "SELECT COUNT(*) FROM working_memory WHERE expires_at > ?", (now_val,)
        ).fetchone()[0]
        slot_per_session = round(slot_total / active_sessions, 1) if active_sessions else 0.0
        episodic_dist = em_repo.db.execute(
            "SELECT event_type, COUNT(*) as cnt FROM episodic_memory GROUP BY event_type ORDER BY cnt DESC"
        ).fetchall()
        recent = em_repo.db.execute("SELECT * FROM episodic_memory ORDER BY created_at DESC LIMIT 10").fetchall()
        return {
            "active_sessions": active_sessions,
            "slot_stats": {"total": slot_total, "avg_per_session": slot_per_session},
            "episodic_distribution": [dict(r) for r in episodic_dist],
            "recent_episodes": [dict(r) for r in recent],
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
            raise _n404("Episodic memories for abstraction")
        txt = "\n".join(f"{r['title']}: {r['description']}" for r in rows)
        msg = [
            {
                "role": "system",
                "content": f'语义抽象层次={abstraction_level}。输出JSON:{{"title":"","content":"","context_tags":[]}}',
            },
            {"role": "user", "content": txt},
        ]
        reply = _call_ai(msg, auth_header).get("reply", "")
        try:
            d = json.loads(reply)
        except Exception:
            d = {
                "title": f"Semantic-{source_type}",
                "content": reply,
                "context_tags": [],
            }
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
        return {"id": eid, "title": d.get("title", ""), "content": d.get("content", "")}

    def semantic_search(self, query: str, limit: int = 10) -> dict:
        kw = f"%{query}%"
        rows = (
            MemoryEntriesRepository(self.db)
            .db.execute(
                "SELECT * FROM memory_entries WHERE memory_type='semantic' AND is_active=1 AND "
                "(title LIKE ? OR content LIKE ?) ORDER BY importance DESC LIMIT ?",
                (kw, kw, limit),
            )
            .fetchall()
        )
        return {"items": [dict(r) for r in rows]}

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
        return {"id": eid, "pattern_name": pattern_name, "success_rate": success_rate}

    def procedural_recall(self, trigger_context: str) -> dict:
        rows = (
            MemoryEntriesRepository(self.db)
            .db.execute(
                "SELECT * FROM memory_entries WHERE memory_type='procedural' AND is_active=1 "
                "ORDER BY importance DESC LIMIT 3"
            )
            .fetchall()
        )
        items = []
        for r in rows:
            try:
                c = json.loads(r["content"])
            except Exception:
                c = {}
            items.append(
                {
                    "id": r["id"],
                    "title": r["title"],
                    "pattern_data": c,
                    "success_rate": r["importance"],
                }
            )
        return {"items": items, "trigger_context": trigger_context}

    def memory_decay(self, hours_threshold: int = 72) -> dict:
        me_repo = MemoryEntriesRepository(self.db)
        cutoff = (datetime.now() - timedelta(hours=hours_threshold)).strftime("%Y-%m-%d %H:%M:%S")
        rows = me_repo.db.execute(
            "SELECT id FROM memory_entries WHERE is_active=1 AND "
            "(last_accessed IS NULL OR last_accessed < ?) AND created_at < ?",
            (cutoff, cutoff),
        ).fetchall()
        for r in rows:
            me_repo.db.execute("UPDATE memory_entries SET is_active=0 WHERE id=?", (r["id"],))
        if rows:
            me_repo.db.commit()
        return {"decayed": len(rows), "hours_threshold": hours_threshold}
