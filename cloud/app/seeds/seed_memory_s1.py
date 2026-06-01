import sqlite3


def seed_memory_s1(conn: sqlite3.Connection) -> None:
    """Insert seed consolidation log record if table is empty."""
    count = conn.execute("SELECT COUNT(*) FROM memory_consolidation_log").fetchone()[0]
    if count > 0:
        return
    now = "2026-05-25 10:00:00"
    conn.execute(
        "INSERT INTO memory_consolidation_log (consolidation_type, item_count, items_promoted, "
        "items_pruned, status, details, created_at) VALUES (?,?,?,?,?,?,?)",
        (
            "sleep_consolidation",
            50,
            8,
            3,
            "completed",
            '{"cycle":"nightly","mode":"auto"}',
            now,
        ),
    )
    conn.commit()
