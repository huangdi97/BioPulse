from cloud.shared.repository import BaseRepository
from shared.columns.memory import TABLE_MEMORY_ASSOCIATIONS_COLS


class MemoryAssociationsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "memory_associations", TABLE_MEMORY_ASSOCIATIONS_COLS)

    def find_by_memory_id(self, memory_id: int, limit: int = 50):
        placeholders = ", ".join(self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE memory_id_a = ? OR memory_id_b = ? ORDER BY weight DESC LIMIT ?",
            (memory_id, memory_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def find_pair(self, id_a: int, id_b: int):
        a, b = (id_a, id_b) if id_a < id_b else (id_b, id_a)
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE memory_id_a = ? AND memory_id_b = ?",
            (a, b),
        ).fetchone()
        return dict(row) if row else None

    def upsert_pair(self, id_a: int, id_b: int, relation_type: str = "related", weight: float = 1.0):
        a, b = (id_a, id_b) if id_a < id_b else (id_b, id_a)
        existing = self.find_pair(id_a, id_b)
        if existing:
            self.db.execute(
                "UPDATE memory_associations SET relation_type = ?, weight = ? WHERE id = ?",
                (relation_type, weight, existing["id"]),
            )
            self.db.commit()
            return existing["id"]
        return self.create(
            {
                "memory_id_a": a,
                "memory_id_b": b,
                "relation_type": relation_type,
                "weight": weight,
            }
        )

    def delete_by_id(self, association_id: int) -> bool:
        return self.delete(association_id)
