"""记忆检索服务，负责工作记忆、情景记忆与语义记忆的查询。"""

import json
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import (
    EpisodicMemoryRepository,
    MemoryConsolidationLogRepository,
    MemoryEntriesRepository,
    WorkingMemoryRepository,
)
from cloud.app.repositories.holographic_repository import MemoryAssociationsRepository
from cloud.app.services.base import BaseService


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _n404(name: str = "Resource") -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{name} not found")


class MemoryRetriever(BaseService):
    """记忆检索服务，提供工作记忆槽位查询、情景记忆列表与语义搜索。"""

    def __init__(self, db):
        super().__init__(db)

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

    def dashboard(self) -> dict:
        now_val = _now()
        wm_repo = WorkingMemoryRepository(self.db)
        em_repo = EpisodicMemoryRepository(self.db)
        active_sessions = wm_repo.db.execute(
            "SELECT COUNT(DISTINCT session_id) FROM working_memory WHERE expires_at > ?",
            (now_val,),
        ).fetchone()[0]
        slot_total = wm_repo.db.execute("SELECT COUNT(*) FROM working_memory WHERE expires_at > ?", (now_val,)).fetchone()[0]
        slot_per_session = round(slot_total / active_sessions, 1) if active_sessions else 0.0
        episodic_dist = em_repo.db.execute("SELECT event_type, COUNT(*) as cnt FROM episodic_memory GROUP BY event_type ORDER BY cnt DESC").fetchall()
        recent = em_repo.db.execute("SELECT * FROM episodic_memory ORDER BY created_at DESC LIMIT 10").fetchall()
        return {
            "active_sessions": active_sessions,
            "slot_stats": {"total": slot_total, "avg_per_session": slot_per_session},
            "episodic_distribution": [dict(r) for r in episodic_dist],
            "recent_episodes": [dict(r) for r in recent],
        }

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

    def procedural_recall(self, trigger_context: str) -> dict:
        rows = (
            MemoryEntriesRepository(self.db)
            .db.execute("SELECT * FROM memory_entries WHERE memory_type='procedural' AND is_active=1 ORDER BY importance DESC LIMIT 3")
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

    def holographic_get(self, memory_id: int, depth: int = 3) -> dict:
        me_repo = MemoryEntriesRepository(self.db)
        entry = me_repo.get_by_id(memory_id)
        if not entry:
            raise _n404(f"Memory entry {memory_id}")
        assoc_repo = MemoryAssociationsRepository(self.db)
        visited = {memory_id}
        root = dict(entry)
        root["associations"] = self._traverse_graph(memory_id, depth, visited, assoc_repo, me_repo)
        return {"entry": root, "depth": depth, "total_nodes": len(visited)}

    def _traverse_graph(self, memory_id: int, depth: int, visited: set, assoc_repo, me_repo, max_per_level: int = 10) -> list:
        if depth <= 0:
            return []
        rows = assoc_repo.find_by_memory_id(memory_id, max_per_level * 2)
        result = []
        count = 0
        for r in rows:
            if count >= max_per_level:
                break
            other_id = r["memory_id_b"] if r["memory_id_a"] == memory_id else r["memory_id_a"]
            if other_id in visited:
                continue
            visited.add(other_id)
            other = me_repo.get_by_id(other_id)
            if not other:
                continue
            node = dict(other)
            node["relation_type"] = r["relation_type"]
            node["weight"] = r["weight"]
            node["associations"] = self._traverse_graph(other_id, depth - 1, visited, assoc_repo, me_repo, max_per_level)
            result.append(node)
            count += 1
        return result
