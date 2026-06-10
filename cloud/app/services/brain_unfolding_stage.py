"""记忆展开与折叠查询阶段。"""

import json


class MemoryUnfoldingStage:
    """读取 cognitive_fold 及其原始来源。"""

    def __init__(self, db):
        self.db = db

    def get_folded(self, memory_id: int) -> dict:
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
            entry = dict(log)
            entry["details"] = json.loads(entry.get("details", "{}"))
            fold_chain.append(entry)

        return {
            "folded": folded,
            "fold_chain": fold_chain,
            "sources": self._read_sources(folded),
        }

    def unfold_memory(self, pattern_id: int) -> list[dict]:
        row = self.db.execute(
            "SELECT * FROM episodic_memory WHERE id=? AND event_type='cognitive_fold'",
            (pattern_id,),
        ).fetchone()
        if not row:
            return []

        return self._read_sources(dict(row))

    def _read_sources(self, folded: dict) -> list[dict]:
        context = json.loads(folded.get("context", "{}"))
        source_ids = context.get("source_ids", [])
        if not source_ids:
            return []

        placeholders = ",".join("?" * len(source_ids))
        episodic_rows = self.db.execute(f"SELECT * FROM episodic_memory WHERE id IN ({placeholders})", source_ids).fetchall()
        sensory_rows = self.db.execute(f"SELECT * FROM sensory_memory WHERE id IN ({placeholders})", source_ids).fetchall()
        procedural_rows = self.db.execute(f"SELECT * FROM procedural_memory WHERE id IN ({placeholders})", source_ids).fetchall()

        result_map = {}
        for r in episodic_rows:
            d = dict(r)
            d["_memory_type"] = "episodic"
            result_map[d["id"]] = d
        for r in sensory_rows:
            d = dict(r)
            if d["id"] not in result_map:
                d["_memory_type"] = "sensory"
                result_map[d["id"]] = d
        for r in procedural_rows:
            d = dict(r)
            if d["id"] not in result_map:
                d["_memory_type"] = "procedural"
                result_map[d["id"]] = d

        return [result_map[sid] for sid in source_ids if sid in result_map]
