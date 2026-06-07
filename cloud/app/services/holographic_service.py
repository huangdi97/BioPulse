import json
from datetime import datetime

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories.holographic_repository import MemoryAssociationsRepository
from cloud.app.repositories.memory_entry_repo import MemoryEntriesRepository
from cloud.app.services.base import BaseService


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _n404(name: str = "Resource") -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{name} not found")


class HolographicService(BaseService):
    def __init__(self, db):
        super().__init__(db)

    def create_association(self, memory_id_a: int, memory_id_b: int, relation_type: str = "related", weight: float = 1.0) -> dict:
        if memory_id_a == memory_id_b:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot associate a memory with itself")
        me_repo = MemoryEntriesRepository(self.db)
        if not me_repo.get_by_id(memory_id_a):
            raise _n404(f"Memory entry {memory_id_a}")
        if not me_repo.get_by_id(memory_id_b):
            raise _n404(f"Memory entry {memory_id_b}")
        repo = MemoryAssociationsRepository(self.db)
        assoc_id = repo.upsert_pair(memory_id_a, memory_id_b, relation_type, weight)
        a, b = (memory_id_a, memory_id_b) if memory_id_a < memory_id_b else (memory_id_b, memory_id_a)
        return {"id": assoc_id, "memory_id_a": a, "memory_id_b": b, "relation_type": relation_type, "weight": weight}

    def get_associations(self, memory_id: int, limit: int = 50) -> list:
        me_repo = MemoryEntriesRepository(self.db)
        if not me_repo.get_by_id(memory_id):
            raise _n404(f"Memory entry {memory_id}")
        repo = MemoryAssociationsRepository(self.db)
        rows = repo.find_by_memory_id(memory_id, limit)
        result = []
        for r in rows:
            other_id = r["memory_id_b"] if r["memory_id_a"] == memory_id else r["memory_id_a"]
            other = me_repo.get_by_id(other_id)
            result.append(
                {
                    "id": r["id"],
                    "memory_id_a": r["memory_id_a"],
                    "memory_id_b": r["memory_id_b"],
                    "relation_type": r["relation_type"],
                    "weight": r["weight"],
                    "related_memory": other,
                }
            )
        return result

    def holographic_graph(self, memory_id: int, depth: int = 3) -> dict:
        me_repo = MemoryEntriesRepository(self.db)
        entry = me_repo.get_by_id(memory_id)
        if not entry:
            raise _n404(f"Memory entry {memory_id}")
        repo = MemoryAssociationsRepository(self.db)
        visited = {memory_id}
        root = dict(entry)
        root["associations"] = self._traverse(memory_id, depth, visited, repo, me_repo)
        return {"entry": root, "depth": depth, "total_nodes": len(visited)}

    def _traverse(self, memory_id: int, depth: int, visited: set, repo, me_repo, max_per_level: int = 10) -> list:
        if depth <= 0:
            return []
        rows = repo.find_by_memory_id(memory_id, max_per_level * 2)
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
            node["associations"] = self._traverse(other_id, depth - 1, visited, repo, me_repo, max_per_level)
            result.append(node)
            count += 1
        return result

    def delete_association(self, association_id: int) -> dict:
        repo = MemoryAssociationsRepository(self.db)
        row = repo.get_by_id(association_id)
        if not row:
            raise _n404("Association")
        repo.delete_by_id(association_id)
        return {"deleted_id": association_id}

    def auto_associate(self, entry_id: int, entry: dict) -> list:
        new_assocs = []
        for method in [self._associate_by_tags, self._associate_by_source, self._associate_by_temporal]:
            try:
                new_assocs.extend(method(entry_id, entry) or [])
            except HTTPException:
                pass
        return new_assocs

    def _associate_by_tags(self, entry_id: int, entry: dict) -> list:
        tags_raw = entry.get("context_tags", "[]")
        if isinstance(tags_raw, str):
            try:
                tags = json.loads(tags_raw)
            except (json.JSONDecodeError, TypeError):
                return []
        elif isinstance(tags_raw, list):
            tags = tags_raw
        else:
            return []
        if not tags:
            return []
        results = []
        me_repo = MemoryEntriesRepository(self.db)
        for tag in tags:
            rows = me_repo.db.execute(
                "SELECT id FROM memory_entries WHERE id != ? AND is_active = 1 AND context_tags LIKE ?",
                (entry_id, f"%{tag}%"),
            ).fetchall()
            for row in rows:
                r = self.create_association(entry_id, row["id"], "shared_tag", 0.8)
                results.append(r)
        return results

    def _associate_by_source(self, entry_id: int, entry: dict) -> list:
        source_id = entry.get("source_id", "")
        if not source_id:
            return []
        me_repo = MemoryEntriesRepository(self.db)
        rows = me_repo.db.execute(
            "SELECT id FROM memory_entries WHERE id != ? AND is_active = 1 AND source_id = ?",
            (entry_id, source_id),
        ).fetchall()
        results = []
        for row in rows:
            r = self.create_association(entry_id, row["id"], "same_source", 0.6)
            results.append(r)
        return results

    def _associate_by_temporal(self, entry_id: int, entry: dict) -> list:
        memory_type = entry.get("memory_type", "")
        if not memory_type:
            return []
        me_repo = MemoryEntriesRepository(self.db)
        rows = me_repo.db.execute(
            "SELECT id FROM memory_entries WHERE id != ? AND is_active = 1 AND memory_type = ? AND date(created_at) = date(?) LIMIT 20",
            (entry_id, memory_type, entry.get("created_at", _now())),
        ).fetchall()
        results = []
        for row in rows:
            r = self.create_association(entry_id, row["id"], "temporal", 0.5)
            results.append(r)
        return results
