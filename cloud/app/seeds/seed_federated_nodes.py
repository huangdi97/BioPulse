import sqlite3


def seed_federated_nodes(conn: sqlite3.Connection) -> None:
    """count = conn.execute("SELECT COUNT(*) FROM federated_nodes").fetchone()[0]"""
    if count > 0:
        return
    now = "2026-05-25 10:00:00"
    conn.execute(
        "INSERT INTO federated_nodes (node_id, node_name, node_type, organization, status, "
        "endpoint_url, public_key, data_summary, last_heartbeat, round_count, total_samples, "
        "reliability_score, is_active, registered_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "node_hospital_a",
            "市第一人民医院",
            "hospital",
            "市第一人民医院",
            "online",
            "https://hospital-a.example.com/fl",
            "",
            '{"departments":["cardiology","oncology"],"record_count":12000}',
            now,
            3,
            1200,
            0.92,
            1,
            now,
            now,
        ),
    )
    conn.execute(
        "INSERT INTO federated_nodes (node_id, node_name, node_type, organization, status, "
        "endpoint_url, public_key, data_summary, last_heartbeat, round_count, total_samples, "
        "reliability_score, is_active, registered_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "node_hospital_b",
            "中山大学附属医院",
            "hospital",
            "中山大学",
            "online",
            "https://hospital-b.example.com/fl",
            "",
            '{"departments":["neurology","pediatrics"],"record_count":8500}',
            now,
            2,
            850,
            0.88,
            1,
            now,
            now,
        ),
    )
    conn.execute(
        "INSERT INTO federated_nodes (node_id, node_name, node_type, organization, status, "
        "endpoint_url, public_key, data_summary, last_heartbeat, round_count, total_samples, "
        "reliability_score, is_active, registered_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "node_lab_c",
            "华大基因合作实验室",
            "research",
            "华大基因",
            "pending",
            "https://lab-c.example.com/fl",
            "",
            '{"focus_areas":["genomics","proteomics"],"sample_count":3200}',
            "",
            0,
            320,
            0.65,
            1,
            now,
            now,
        ),
    )
    conn.commit()
