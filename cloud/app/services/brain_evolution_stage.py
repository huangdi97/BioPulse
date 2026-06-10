"""单条记忆演化阶段。"""

from datetime import datetime

TABLE_MAP = {
    "episodic": "episodic_memory",
    "sensory": "sensory_memory",
    "procedural": "procedural_memory",
}

ALLOWED_FIELDS = {
    "episodic": {"title", "description", "context", "outcome", "valence", "intensity"},
    "sensory": {"raw_content", "importance"},
    "procedural": {"name", "description", "steps", "trigger_conditions"},
}


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calc_confidence(memory_type: str, importance: float, valence: float = 0.0) -> float:
    base = importance * 0.6 + abs(valence) * 0.4
    if memory_type == "episodic":
        return round(min(base * 1.1, 1.0), 4)
    return round(min(base, 1.0), 4)


class MemoryEvolutionStage:
    """处理新证据合并与演化日志。"""

    def __init__(self, db):
        self.db = db

    def read_memory(self, memory_id: int, memory_type: str) -> dict | None:
        table = TABLE_MAP.get(memory_type)
        if not table:
            return None
        row = self.db.execute(f"SELECT * FROM {table} WHERE id=?", (memory_id,)).fetchone()
        return dict(row) if row else None

    def update_memory_field(self, memory_id: int, memory_type: str, field: str, new_value: str) -> bool:
        table = TABLE_MAP.get(memory_type)
        if not table:
            return False
        allowed = ALLOWED_FIELDS.get(memory_type, set())
        if field not in allowed:
            return False
        quoted = f'"{field}"'
        self.db.execute(
            f"UPDATE {table} SET {quoted}=?, updated_at=? WHERE id=?",
            (new_value, now_str(), memory_id),
        )
        return True

    def evolve_memory(self, memory_id: int, new_evidence: str, memory_type: str = "episodic") -> dict:
        memory = self.read_memory(memory_id, memory_type)
        if not memory:
            return {"error": f"{memory_type} memory #{memory_id} not found"}

        field = "description"
        old_value = str(memory.get(field, ""))
        merged = f"{old_value}\n[evolved] {new_evidence}" if old_value else new_evidence
        merged = merged[:1000]

        confidence_before = calc_confidence(memory_type, memory.get("importance", 0.5), memory.get("valence", 0.0))
        confidence_after = calc_confidence(memory_type, memory.get("importance", 0.5) + 0.05, memory.get("valence", 0.0) + 0.05)
        confidence_after = min(confidence_after + 0.05, 1.0)

        ok = self.update_memory_field(memory_id, memory_type, field, merged)
        if not ok:
            return {"error": f"failed to update field '{field}' on {memory_type} memory"}

        self.db.execute(
            "INSERT INTO memory_evolution_log (memory_id, memory_type, field_changed, old_value, new_value, trigger, confidence_before, confidence_after) VALUES (?,?,?,?,?,?,?,?)",
            (
                memory_id,
                memory_type,
                field,
                old_value[:500],
                merged[:500],
                "new_evidence",
                confidence_before,
                confidence_after,
            ),
        )
        self.db.commit()
        return {
            "memory_id": memory_id,
            "memory_type": memory_type,
            "field_changed": field,
            "confidence_before": confidence_before,
            "confidence_after": confidence_after,
            "status": "evolved",
        }

    def get_evolution_history(self, memory_id: int) -> list[dict]:
        rows = self.db.execute(
            "SELECT * FROM memory_evolution_log WHERE memory_id=? ORDER BY evolved_at DESC",
            (memory_id,),
        ).fetchall()
        return [dict(r) for r in rows]
