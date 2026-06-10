"""记忆折叠压缩阶段。"""

import json
from datetime import datetime


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class MemoryFoldingStage:
    """将多源记忆压缩为 cognitive_fold 情景记忆。"""

    def __init__(self, db):
        self.db = db

    def fold_memories(self, memory_ids: list[int]) -> dict:
        if not memory_ids:
            return {"error": "no valid memory_ids found", "memory_ids": memory_ids}

        placeholders = ",".join("?" * len(memory_ids))
        episodic_rows = self.db.execute(f"SELECT * FROM episodic_memory WHERE id IN ({placeholders})", memory_ids).fetchall()
        sensory_rows = self.db.execute(f"SELECT * FROM sensory_memory WHERE id IN ({placeholders})", memory_ids).fetchall()
        procedural_rows = self.db.execute(f"SELECT * FROM procedural_memory WHERE id IN ({placeholders})", memory_ids).fetchall()

        episodic_dict = {r["id"]: dict(r) for r in episodic_rows}
        sensory_dict = {r["id"]: dict(r) for r in sensory_rows}
        procedural_dict = {r["id"]: dict(r) for r in procedural_rows}

        sources = []
        descriptions = []
        total_importance = 0.0
        total_valence = 0.0
        valence_count = 0

        for mid in memory_ids:
            if mid in episodic_dict:
                row = episodic_dict[mid]
                sources.append({"memory_id": mid, "memory_type": "episodic", "table": "episodic_memory"})
                descriptions.append(row.get("title", "") + ": " + row.get("description", ""))
                total_importance += 0.5
                total_valence += row.get("valence", 0.0)
                valence_count += 1
            elif mid in sensory_dict:
                row = sensory_dict[mid]
                sources.append({"memory_id": mid, "memory_type": "sensory", "table": "sensory_memory"})
                descriptions.append(row.get("raw_content", ""))
                total_importance += row.get("importance", 0.5)
            elif mid in procedural_dict:
                row = procedural_dict[mid]
                sources.append({"memory_id": mid, "memory_type": "procedural", "table": "procedural_memory"})
                descriptions.append(row.get("name", "") + ": " + row.get("description", ""))
                total_importance += 0.5

        if not sources:
            return {"error": "no valid memory_ids found", "memory_ids": memory_ids}

        avg_importance = round(total_importance / len(sources), 2)
        avg_valence = round(total_valence / valence_count, 2) if valence_count > 0 else 0.0
        abstract_title = f"Cognitive Fold ({len(sources)} memories)"
        abstract_desc = " | ".join(filter(None, descriptions))[:1000]
        n = now_str()

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
