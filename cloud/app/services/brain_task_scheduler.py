"""Task scheduling logic for brain orchestrator — sensory ingestion and orchestration flow."""

import json
import random
from datetime import datetime, timedelta


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
            return round(random.uniform(lo, hi), 2)
    return round(random.uniform(0.1, 0.3), 2)


def schedule_sensory(db, input_type: str, raw_content: str, source: str) -> dict:
    importance = _calc_importance(raw_content)
    n = _now()
    expires_at = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    cur = db.execute(
        "INSERT INTO sensory_memory (input_type, raw_content, source, importance, expires_at, created_at) VALUES (?,?,?,?,?,?)",
        (input_type, raw_content, source, importance, expires_at, n),
    )
    sid = cur.lastrowid
    routed_to = ["sensory_memory"]
    if importance > 0.6:
        db.execute(
            "INSERT OR REPLACE INTO working_memory (session_id, slot_key, slot_value, slot_type, ttl_seconds, created_at, expires_at) VALUES (?,?,?,?,?,?,?)",
            ("brain_orchestrator", f"sensory_{sid}", raw_content[:500], "string", 1800, n, expires_at),
        )
        db.execute(
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
        db.execute(
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
    db.commit()
    return {"sensory_id": sid, "importance": importance, "processed": 0, "routed_to": routed_to}


def orchestrator_flow(db, input_text: str, input_type: str, source: str) -> dict:
    n = _now()
    sensory = schedule_sensory(db, input_type, input_text, source)
    working = [
        dict(r)
        for r in db.execute(
            "SELECT * FROM working_memory WHERE session_id=? AND expires_at>? ORDER BY created_at DESC LIMIT 5",
            ("brain_orchestrator", n),
        ).fetchall()
    ]
    episodic = [dict(r) for r in db.execute("SELECT * FROM episodic_memory ORDER BY valence DESC LIMIT 5").fetchall()]
    kg_rows = db.execute(
        "SELECT * FROM kg_entities WHERE name LIKE ? OR entity_type LIKE ? LIMIT 5",
        (f"%{input_text[:20]}%", f"%{input_text[:20]}%"),
    ).fetchall()
    semantic_kv = [dict(r) for r in kg_rows] if kg_rows else []
    proc_rows = db.execute("SELECT * FROM procedural_memory WHERE invocation_count > 0 ORDER BY invocation_count DESC LIMIT 3").fetchall()
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
