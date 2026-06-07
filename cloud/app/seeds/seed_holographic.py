import sqlite3


def seed_holographic(conn: sqlite3.Connection) -> None:
    count = conn.execute("SELECT COUNT(*) FROM memory_associations").fetchone()[0]
    if count > 0:
        return
    entries = conn.execute("SELECT id FROM memory_entries WHERE is_active = 1 LIMIT 50").fetchall()
    ids = [r["id"] for r in entries]
    if len(ids) < 2:
        return
    for i, id_a in enumerate(ids):
        for j in range(i + 1, min(i + 4, len(ids))):
            id_b = ids[j]
            a, b = (id_a, id_b) if id_a < id_b else (id_b, id_a)
            conn.execute(
                "INSERT OR IGNORE INTO memory_associations (memory_id_a, memory_id_b, relation_type, weight) VALUES (?, ?, ?, ?)",
                (a, b, "related", 0.7),
            )
    conn.commit()
