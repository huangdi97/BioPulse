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

        result = []
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
                    result.append(r)
                    break

        return result
