import sqlite3


def seed_world_tree(conn: sqlite3.Connection) -> None:
    """Insert default world tree nodes and node-memory links if tables are empty."""
    count = conn.execute("SELECT COUNT(*) FROM world_tree_nodes").fetchone()[0]
    if count > 0:
        return
    now = "2026-05-25 10:00:00"
    nodes = [
        ("医药知识库", "根节点：医药知识体系总入口", None, "/医药知识库", 0, "root", 0),
        ("肿瘤学", "肿瘤学相关知识领域", 1, "/医药知识库/肿瘤学", 1, "domain", 10),
        ("心血管", "心血管相关知识领域", 1, "/医药知识库/心血管", 1, "domain", 20),
        (
            "竞品分析",
            "竞品分析相关记忆条目",
            3,
            "/医药知识库/心血管/竞品分析",
            2,
            "tag",
            10,
        ),
        (
            "学术推广",
            "学术推广相关记忆条目",
            3,
            "/医药知识库/心血管/学术推广",
            2,
            "tag",
            20,
        ),
    ]
    node_ids = []
    for name, desc, parent_id, path, level, node_type, sort_order in nodes:
        cur = conn.execute(
            "INSERT INTO world_tree_nodes (name, description, parent_id, path, level, node_type, sort_order, "
            "created_by, created_at, updated_at) VALUES (?,?,?,?,?,?,?,1,?,?)",
            (name, desc, parent_id, path, level, node_type, sort_order, now, now),
        )
        node_ids.append(cur.lastrowid)
    links = [
        (node_ids[3], 1, 0.9),
        (node_ids[3], 3, 0.7),
        (node_ids[4], 2, 0.8),
        (node_ids[4], 4, 0.6),
        (node_ids[4], 5, 0.85),
    ]
    for node_id, memory_id, relevance in links:
        conn.execute(
            "INSERT OR IGNORE INTO node_memory_links (node_id, memory_entry_id, relevance_score, created_at) VALUES (?,?,?,?)",
            (node_id, memory_id, relevance, now),
        )
    conn.commit()
