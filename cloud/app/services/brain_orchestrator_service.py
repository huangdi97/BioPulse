"""脑编排服务，承接感知输入并协调多类型记忆存储与编排推理。"""

import json
from datetime import datetime, timedelta

from cloud.app.services.base import BaseService


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


KEYWORD_MAP = [
    (["urgent", "紧急", "违规", "violation"], 0.85, 0.9),
    (["商机", "签约", "opportunity", "deal"], 0.75, 0.85),
    (["投诉", "complain", "风险", "risk"], 0.7, 0.8),
]


def _calc_importance(text: str) -> float:
    lower = text.lower()
    for keywords, lo, hi in KEYWORD_MAP:
        if any(kw in lower or kw in text for kw in keywords):
            import random

            return round(random.uniform(lo, hi), 2)
    return round(random.uniform(0.1, 0.3), 2)


class BrainOrchestratorService(BaseService):
    """BrainOrchestrator 服务类。"""

    def ingest_sensory(self, input_type: str, raw_content: str, source: str) -> dict:
        """ingest_sensory 操作。

        Args:
            input_type: 描述
            raw_content: 描述
            source: 描述

        Returns:
            描述
        """
        importance = _calc_importance(raw_content)
        n = _now()
        expires_at = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        cur = self.db.execute(
            "INSERT INTO sensory_memory (input_type, raw_content, source, importance, expires_at, created_at) VALUES (?,?,?,?,?,?)",
            (input_type, raw_content, source, importance, expires_at, n),
        )
        sid = cur.lastrowid
        routed_to = ["sensory_memory"]
        if importance > 0.6:
            self.db.execute(
                "INSERT OR REPLACE INTO working_memory (session_id, slot_key, slot_value, slot_type, ttl_seconds, created_at, expires_at) VALUES (?,?,?,?,?,?,?)",
                ("brain_orchestrator", f"sensory_{sid}", raw_content[:500], "string", 1800, n, expires_at),
            )
            self.db.execute(
                "INSERT INTO memory_consolidation_log (consolidation_type, source_table, item_count, items_promoted, status, details, created_at) VALUES (?,?,?,?,?,?,?)",
                (
                    "sensory_promotion",
                    "sensory_memory",
                    1,
                    1,
                    "completed",
                    json.dumps({"sensory_id": sid, "importance": importance}, ensure_ascii=False),
                    n,
                ),
            )
            routed_to.append("working_memory")
        if importance > 0.8:
            self.db.execute(
                "INSERT INTO episodic_memory (event_type, title, description, context, outcome, valence, intensity, created_by, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    "sensory_triggered",
                    f"Sensory->Episodic #{sid}",
                    raw_content[:300],
                    json.dumps({"source": source, "sensory_id": sid}, ensure_ascii=False),
                    "auto_ingested",
                    importance,
                    0.6,
                    "0",
                    n,
                ),
            )
            routed_to.append("episodic_memory")
        self.db.commit()
        return {"sensory_id": sid, "importance": importance, "processed": 0, "routed_to": routed_to}

    def get_sensory_buffer(self, limit: int = 50) -> list[dict]:
        """get_sensory_buffer 操作。

        Args:
            limit: 描述

        Returns:
            描述
        """
        n = _now()
        rows = self.db.execute(
            "SELECT * FROM sensory_memory WHERE (expires_at = '' OR expires_at > ?) ORDER BY importance DESC LIMIT ?",
            (n, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_procedural(self, trigger_event: str | None = None) -> list[dict]:
        """list_procedural 操作。

        Args:
            trigger_event: 描述

        Returns:
            描述
        """
        if trigger_event:
            rows = self.db.execute(
                "SELECT * FROM procedural_memory WHERE trigger_conditions LIKE ? ORDER BY invocation_count DESC",
                (f"%{trigger_event}%",),
            ).fetchall()
        else:
            rows = self.db.execute("SELECT * FROM procedural_memory ORDER BY invocation_count DESC").fetchall()
        return [dict(r) for r in rows]

    def create_procedural(self, procedure_key: str, name: str, description: str, steps: str, trigger_conditions: str) -> dict:
        """create_procedural 操作。

        Args:
            procedure_key: 描述
            name: 描述
            description: 描述
            steps: 描述
            trigger_conditions: 描述

        Returns:
            描述
        """
        n = _now()
        self.db.execute(
            "INSERT INTO procedural_memory (procedure_key, name, description, steps, trigger_conditions, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            (procedure_key, name, description, steps, trigger_conditions, n, n),
        )
        self.db.commit()
        return {"procedure_key": procedure_key, "name": name, "created_at": n}

    def invoke_procedural(self, procedure_key: str, context: dict) -> dict:
        """invoke_procedural 操作。

        Args:
            procedure_key: 描述
            context: 描述

        Returns:
            描述
        """
        row = self.db.execute("SELECT * FROM procedural_memory WHERE procedure_key=?", (procedure_key,)).fetchone()
        if not row:
            return {"error": f"procedure '{procedure_key}' not found"}
        row = dict(row)
        n = _now()
        new_count = (row["invocation_count"] or 0) + 1
        self.db.execute(
            "UPDATE procedural_memory SET invocation_count=?, last_invoked_at=?, updated_at=? WHERE procedure_key=?",
            (new_count, n, n, procedure_key),
        )
        self.db.commit()
        steps_data = json.loads(row["steps"]) if isinstance(row["steps"], str) else row["steps"]
        return {
            "procedure_key": procedure_key,
            "name": row["name"],
            "steps": steps_data,
            "step_count": len(steps_data),
            "invocation_count": new_count,
            "last_invoked_at": n,
            "context": context,
            "status": "ready",
        }

    def orchestrate(self, input_text: str, input_type: str, source: str) -> dict:
        """orchestrate 操作。

        Args:
            input_text: 描述
            input_type: 描述
            source: 描述

        Returns:
            描述
        """
        n = _now()
        sensory = self.ingest_sensory(input_type, input_text, source)
        working = [
            dict(r)
            for r in self.db.execute(
                "SELECT * FROM working_memory WHERE session_id=? AND expires_at>? ORDER BY created_at DESC LIMIT 5",
                ("brain_orchestrator", n),
            ).fetchall()
        ]
        episodic = [dict(r) for r in self.db.execute("SELECT * FROM episodic_memory ORDER BY valence DESC LIMIT 5").fetchall()]
        kg_rows = self.db.execute(
            "SELECT * FROM kg_entities WHERE name LIKE ? OR entity_type LIKE ? LIMIT 5",
            (f"%{input_text[:20]}%", f"%{input_text[:20]}%"),
        ).fetchall()
        semantic_kv = [dict(r) for r in kg_rows] if kg_rows else []
        proc_rows = self.db.execute("SELECT * FROM procedural_memory WHERE invocation_count > 0 ORDER BY invocation_count DESC LIMIT 3").fetchall()
        procedural = [dict(r) for r in proc_rows]
        valences = [e.get("valence", 0.0) or 0.0 for e in episodic]
        avg_valence = sum(valences) / len(valences) if valences else 0.0
        if avg_valence > 0.3:
            emotional = {"mood": "positive", "valence": round(avg_valence, 2), "utility": 0.7, "label": "积极"}
        elif avg_valence < -0.3:
            emotional = {"mood": "negative", "valence": round(avg_valence, 2), "utility": 0.3, "label": "消极"}
        else:
            emotional = {"mood": "neutral", "valence": round(avg_valence, 2), "utility": 0.5, "label": "中性"}
        return {
            "sensory": sensory,
            "working": working,
            "episodic": episodic,
            "semantic": semantic_kv,
            "procedural": procedural,
            "emotional": emotional,
        }

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
