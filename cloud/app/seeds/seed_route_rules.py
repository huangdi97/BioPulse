import sqlite3


def seed_route_rules(conn: sqlite3.Connection) -> None:
    """Insert preset routing rules if table is empty."""
    count = conn.execute("SELECT COUNT(*) FROM route_rules").fetchone()[0]
    if count > 0:
        return
    now = "2026-05-25 10:00:00"
    roles = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM agent_roles WHERE is_active=1").fetchall()}
    rules = [
        (
            "竞品相关",
            10,
            "keyword",
            "contains",
            "竞品",
            roles.get("情报分析师Agent"),
            None,
            now,
        ),
        (
            "策略相关",
            20,
            "keyword",
            "contains",
            "策略",
            roles.get("策略规划Agent"),
            None,
            now,
        ),
        (
            "销售话术",
            30,
            "keyword",
            "contains",
            "销售话术",
            roles.get("销售代表Agent"),
            None,
            now,
        ),
        (
            "培训相关",
            40,
            "keyword",
            "contains",
            "培训",
            roles.get("复盘分析师Agent"),
            None,
            now,
        ),
        (
            "政策相关",
            50,
            "keyword",
            "contains",
            "政策",
            roles.get("情报分析师Agent"),
            None,
            now,
        ),
        ("兜底", 999, "keyword", "contains", "", roles.get("策略规划Agent"), None, now),
    ]
    for name, pri, cf, co, cv, tid, fid, ts in rules:
        conn.execute(
            "INSERT INTO route_rules (name, priority, condition_field, condition_operator, "
            "condition_value, target_role_id, fallback_role_id, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (name, pri, cf, co, cv, tid, fid, ts, ts),
        )
    conn.commit()
