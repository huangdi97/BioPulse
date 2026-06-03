import json
from datetime import datetime

from cloud.app.services.base import BaseService


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _calc_confidence(memory_type: str, importance: float, valence: float = 0.0) -> float:
    base = importance * 0.6 + abs(valence) * 0.4
    if memory_type == "episodic":
        return round(min(base * 1.1, 1.0), 4)
    return round(min(base, 1.0), 4)


class BrainEvolutionService(BaseService):
    """BrainEvolution 服务类。"""

    def _read_memory(self, memory_id: int, memory_type: str) -> dict | None:
        table_map = {
            "episodic": "episodic_memory",
            "sensory": "sensory_memory",
            "procedural": "procedural_memory",
        }
        table = table_map.get(memory_type)
        if not table:
            return None
        row = self.db.execute(f"SELECT * FROM {table} WHERE id=?", (memory_id,)).fetchone()
        return dict(row) if row else None

    def _update_memory_field(self, memory_id: int, memory_type: str, field: str, new_value: str) -> bool:
        table_map = {
            "episodic": "episodic_memory",
            "sensory": "sensory_memory",
            "procedural": "procedural_memory",
        }
        table = table_map.get(memory_type)
        if not table:
            return False
        allowed_fields = {
            "episodic": {"title", "description", "context", "outcome", "valence", "intensity"},
            "sensory": {"raw_content", "importance"},
            "procedural": {"name", "description", "steps", "trigger_conditions"},
        }
        allowed = allowed_fields.get(memory_type, set())
        if field not in allowed:
            return False
        quoted = f'"{field}"'
        self.db.execute(
            f"UPDATE {table} SET {quoted}=?, updated_at=? WHERE id=?",
            (new_value, _now(), memory_id),
        )
        return True

    def evolve_memory(self, memory_id: int, new_evidence: str, memory_type: str = "episodic") -> dict:
        """evolve_memory 操作。

        Args:
            memory_id: 描述
            new_evidence: 描述
            memory_type: 描述

        Returns:
            描述
        """
        memory = self._read_memory(memory_id, memory_type)
        if not memory:
            return {"error": f"{memory_type} memory #{memory_id} not found"}

        field = "description"
        old_value = str(memory.get(field, ""))
        merged = f"{old_value}\n[evolved] {new_evidence}" if old_value else new_evidence
        merged = merged[:1000]

        confidence_before = _calc_confidence(memory_type, memory.get("importance", 0.5), memory.get("valence", 0.0))
        confidence_after = _calc_confidence(
            memory_type, memory.get("importance", 0.5) + 0.05, memory.get("valence", 0.0) + 0.05
        )
        confidence_after = min(confidence_after + 0.05, 1.0)

        ok = self._update_memory_field(memory_id, memory_type, field, merged)
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
        """get_evolution_history 操作。

        Args:
            memory_id: 描述

        Returns:
            描述
        """
        rows = self.db.execute(
            "SELECT * FROM memory_evolution_log WHERE memory_id=? ORDER BY evolved_at DESC",
            (memory_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def fold_memories(self, memory_ids: list[int]) -> dict:
        """fold_memories 操作。

        Args:
            memory_ids: 描述

        Returns:
            描述
        """
        sources = []
        descriptions = []
        total_importance = 0.0
        total_valence = 0.0
        valence_count = 0

        for mid in memory_ids:
            row = self.db.execute("SELECT * FROM episodic_memory WHERE id=?", (mid,)).fetchone()
            if row:
                row = dict(row)
                sources.append({"memory_id": mid, "memory_type": "episodic", "table": "episodic_memory"})
                descriptions.append(row.get("title", "") + ": " + row.get("description", ""))
                total_importance += 0.5
                total_valence += row.get("valence", 0.0)
                valence_count += 1
                continue
            row = self.db.execute("SELECT * FROM sensory_memory WHERE id=?", (mid,)).fetchone()
            if row:
                row = dict(row)
                sources.append({"memory_id": mid, "memory_type": "sensory", "table": "sensory_memory"})
                descriptions.append(row.get("raw_content", ""))
                total_importance += row.get("importance", 0.5)
                continue
            row = self.db.execute("SELECT * FROM procedural_memory WHERE id=?", (mid,)).fetchone()
            if row:
                row = dict(row)
                sources.append({"memory_id": mid, "memory_type": "procedural", "table": "procedural_memory"})
                descriptions.append(row.get("name", "") + ": " + row.get("description", ""))
                total_importance += 0.5

        if not sources:
            return {"error": "no valid memory_ids found", "memory_ids": memory_ids}

        avg_importance = round(total_importance / len(sources), 2)
        avg_valence = round(total_valence / valence_count, 2) if valence_count > 0 else 0.0
        abstract_title = f"Cognitive Fold ({len(sources)} memories)"
        abstract_desc = " | ".join(filter(None, descriptions))[:1000]
        n = _now()

        cur = self.db.execute(
            "INSERT INTO episodic_memory (event_type, title, description, context, outcome, valence, intensity, created_by, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (
                "cognitive_fold",
                abstract_title,
                abstract_desc,
                json.dumps({"source_ids": memory_ids, "sources": sources}, ensure_ascii=False),
                "folded",
                avg_valence,
                avg_importance,
                "brain_orchestrator",
                n,
            ),
        )
        folded_id = cur.lastrowid

        self.db.execute(
            "INSERT INTO memory_consolidation_log (consolidation_type, source_table, item_count, items_promoted, status, details, created_at) VALUES (?,?,?,?,?,?,?)",
            (
                "cognitive_fold",
                "mixed",
                len(sources),
                folded_id,
                "completed",
                json.dumps({"source_ids": memory_ids, "avg_importance": avg_importance}, ensure_ascii=False),
                n,
            ),
        )
        self.db.commit()

        return {
            "folded_id": folded_id,
            "title": abstract_title,
            "description": abstract_desc[:200],
            "source_count": len(sources),
            "source_ids": memory_ids,
            "avg_importance": avg_importance,
        }

    def get_folded(self, memory_id: int) -> dict:
        """get_folded 操作。

        Args:
            memory_id: 描述

        Returns:
            描述
        """
        row = self.db.execute(
            "SELECT * FROM episodic_memory WHERE id=? AND event_type='cognitive_fold'",
            (memory_id,),
        ).fetchone()
        if not row:
            return {"error": f"cognitive fold #{memory_id} not found"}

        folded = dict(row)

        logs = self.db.execute(
            "SELECT * FROM memory_consolidation_log WHERE consolidation_type='cognitive_fold' AND items_promoted=? ORDER BY created_at DESC",
            (memory_id,),
        ).fetchall()

        fold_chain = []
        for log in logs:
            l = dict(log)
            l["details"] = json.loads(l.get("details", "{}"))
            fold_chain.append(l)

        context = json.loads(folded.get("context", "{}"))
        source_ids = context.get("source_ids", [])
        sources = []
        for sid in source_ids:
            for table, mtype in [
                ("episodic_memory", "episodic"),
                ("sensory_memory", "sensory"),
                ("procedural_memory", "procedural"),
            ]:
                r = self.db.execute(f"SELECT * FROM {table} WHERE id=?", (sid,)).fetchone()
                if r:
                    r = dict(r)
                    r["_memory_type"] = mtype
                    sources.append(r)
                    break

        return {
            "folded": folded,
            "fold_chain": fold_chain,
            "sources": sources,
        }
