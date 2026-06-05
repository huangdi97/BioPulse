import json
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.services.base import BaseService


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class UnifiedMemoryService(BaseService):
    def __init__(self, db):
        super().__init__(db)
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS unified_memory ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "title TEXT NOT NULL DEFAULT '', "
            "content TEXT NOT NULL DEFAULT '', "
            "discipline TEXT NOT NULL DEFAULT '', "
            "tags TEXT DEFAULT '[]', "
            "source_id TEXT DEFAULT '', "
            "created_at TEXT DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_um_discipline ON unified_memory(discipline)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_um_source ON unified_memory(source_id)")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS unified_memory_links ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "source_id INTEGER NOT NULL, "
            "target_id INTEGER NOT NULL, "
            "relation_type TEXT NOT NULL DEFAULT '', "
            "created_at TEXT DEFAULT CURRENT_TIMESTAMP, "
            "FOREIGN KEY (source_id) REFERENCES unified_memory(id), "
            "FOREIGN KEY (target_id) REFERENCES unified_memory(id)"
            ")"
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_uml_source ON unified_memory_links(source_id)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_uml_target ON unified_memory_links(target_id)")
        self.db.commit()

    def create_memory(
        self,
        title: str,
        content: str,
        discipline: str,
        tags: Optional[List[str]] = None,
        source_id: str = "",
    ) -> dict:
        if not title:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Title is required",
            )
        if not discipline:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Discipline is required",
            )
        tags_json = json.dumps(tags or [], ensure_ascii=False)
        now = _now()
        cursor = self.db.execute(
            "INSERT INTO unified_memory (title, content, discipline, tags, source_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (title, content, discipline, tags_json, source_id, now),
        )
        self.db.commit()
        memory_id = cursor.lastrowid
        return {
            "id": memory_id,
            "title": title,
            "content": content,
            "discipline": discipline,
            "tags": tags or [],
            "source_id": source_id,
            "created_at": now,
        }

    def link_memories(
        self,
        memory_id_1: int,
        memory_id_2: int,
        relation_type: str,
    ) -> dict:
        if memory_id_1 == memory_id_2:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Cannot link a memory to itself",
            )
        row1 = self.db.execute("SELECT id FROM unified_memory WHERE id=?", (memory_id_1,)).fetchone()
        if not row1:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=f"Memory {memory_id_1} not found",
            )
        row2 = self.db.execute("SELECT id FROM unified_memory WHERE id=?", (memory_id_2,)).fetchone()
        if not row2:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=f"Memory {memory_id_2} not found",
            )
        existing = self.db.execute(
            "SELECT id FROM unified_memory_links WHERE (source_id=? AND target_id=?) OR (source_id=? AND target_id=?)",
            (memory_id_1, memory_id_2, memory_id_2, memory_id_1),
        ).fetchone()
        if existing:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="A link between these memories already exists",
            )
        now = _now()
        cursor = self.db.execute(
            "INSERT INTO unified_memory_links (source_id, target_id, relation_type, created_at) VALUES (?, ?, ?, ?)",
            (memory_id_1, memory_id_2, relation_type, now),
        )
        self.db.commit()
        return {
            "id": cursor.lastrowid,
            "source_id": memory_id_1,
            "target_id": memory_id_2,
            "relation_type": relation_type,
            "created_at": now,
        }

    def search_by_discipline(self, discipline: str) -> List[dict]:
        rows = self.db.execute(
            "SELECT id, title, content, discipline, tags, source_id, created_at FROM unified_memory WHERE discipline=? ORDER BY created_at DESC",
            (discipline,),
        ).fetchall()
        results = []
        for r in rows:
            try:
                tags = json.loads(r["tags"]) if r["tags"] else []
            except (json.JSONDecodeError, TypeError):
                tags = []
            results.append(
                {
                    "id": r["id"],
                    "title": r["title"],
                    "content": r["content"],
                    "discipline": r["discipline"],
                    "tags": tags,
                    "source_id": r["source_id"],
                    "created_at": r["created_at"],
                }
            )
        return results

    def get_cross_discipline_links(self, memory_id: int) -> List[dict]:
        mem = self.db.execute("SELECT id, discipline FROM unified_memory WHERE id=?", (memory_id,)).fetchone()
        if not mem:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=f"Memory {memory_id} not found",
            )
        rows = self.db.execute(
            "SELECT uml.id, uml.source_id, uml.target_id, uml.relation_type, uml.created_at, "
            "src.discipline AS source_discipline, "
            "tgt.discipline AS target_discipline "
            "FROM unified_memory_links uml "
            "JOIN unified_memory src ON uml.source_id = src.id "
            "JOIN unified_memory tgt ON uml.target_id = tgt.id "
            "WHERE uml.source_id=? OR uml.target_id=? "
            "ORDER BY uml.created_at DESC",
            (memory_id, memory_id),
        ).fetchall()
        results = []
        for r in rows:
            results.append(
                {
                    "id": r["id"],
                    "source_id": r["source_id"],
                    "target_id": r["target_id"],
                    "relation_type": r["relation_type"],
                    "source_discipline": r["source_discipline"],
                    "target_discipline": r["target_discipline"],
                    "is_cross_discipline": r["source_discipline"] != r["target_discipline"],
                    "created_at": r["created_at"],
                }
            )
        return results

    def get_all_disciplines(self) -> List[str]:
        rows = self.db.execute("SELECT DISTINCT discipline FROM unified_memory WHERE discipline != '' ORDER BY discipline").fetchall()
        return [r["discipline"] for r in rows]
