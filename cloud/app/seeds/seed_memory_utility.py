import sqlite3


def seed_memory_utility(conn: sqlite3.Connection) -> None:
    """Insert preset utility scores for the first 5 memory entries if table is empty."""
    count = conn.execute("SELECT COUNT(*) FROM memory_utility_scores").fetchone()[0]
    if count > 0:
        return
    from datetime import datetime as _dt

    entries = conn.execute(
        "SELECT id, importance, access_count, last_accessed FROM memory_entries ORDER BY id LIMIT 5"
    ).fetchall()
    if not entries:
        return
    now = "2026-05-25 10:00:00"
    for entry in entries:
        mid = entry["id"]
        imp = entry["importance"]
        ac = entry["access_count"] or 0
        la = entry["last_accessed"]
        conn_count = conn.execute(
            "SELECT COUNT(*) FROM node_memory_links WHERE memory_entry_id=?", (mid,)
        ).fetchone()[0]
        access_freq = min(ac / 100.0, 1.0)
        if la is None:
            recency = 0.2
        else:
            days_ago = (_dt.now() - _dt.strptime(la, "%Y-%m-%d %H:%M:%S")).days
            recency = 1.0 if days_ago <= 7 else (0.5 if days_ago <= 30 else 0.2)
        connectivity = min(conn_count / 5.0, 1.0)
        utility = 0.3 * imp + 0.3 * access_freq + 0.2 * recency + 0.2 * connectivity
        decay = round(1.0 - utility, 4)
        utility = round(utility, 4)
        conn.execute(
            "INSERT INTO memory_utility_scores (memory_entry_id, utility_score, access_frequency, "
            "recency_score, importance_score, connectivity_score, decay_rate, last_utility_update, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (mid, utility, access_freq, recency, imp, connectivity, decay, now, now),
        )
    conn.commit()
