import sqlite3


def seed_a2a(conn: sqlite3.Connection) -> None:
    """count = conn.execute("SELECT COUNT(*) FROM agent_registry").fetchone()[0]"""
    if count > 0:
        return

    agents = [
        (
            "copilot_market_intel",
            "市场情报Agent",
            "intel",
            '["market_analyze","competitor_tracking","trend_forecast"]',
            "online",
        ),
        (
            "copilot_compliance",
            "合规检查Agent",
            "compliance",
            '["compliance_check","redline_scan","policy_review"]',
            "online",
        ),
        ("copilot_hcp_outreach", "HCP触达Agent", "outreach", '["hcp_profile","strategy_gen","visit_plan"]', "offline"),
    ]
    conn.executemany(
        "INSERT INTO agent_registry (agent_key, agent_name, agent_type, capabilities, status) VALUES (?, ?, ?, ?, ?)",
        agents,
    )

    task_count = conn.execute("SELECT COUNT(*) FROM agent_tasks").fetchone()[0]
    if task_count == 0:
        conn.execute(
            "INSERT INTO agent_tasks (task_id, source_agent_key, target_agent_key, task_type, input_data, output_data, status, completed_at, duration_ms) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "a2a:seed-001",
                "copilot_market_intel",
                "copilot_compliance",
                "compliance_check",
                '{"doc":"市场材料v3"}',
                '{"passed":true,"issues":[]}',
                "completed",
                "2026-06-01 10:00:00",
                1200,
            ),
        )
        conn.execute(
            "INSERT INTO agent_tasks (task_id, source_agent_key, target_agent_key, task_type, input_data, status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                "a2a:seed-002",
                "copilot_hcp_outreach",
                "copilot_market_intel",
                "market_analyze",
                '{"hcp":"Dr.Li","region":"华东"}',
                "running",
            ),
        )

    event_count = conn.execute("SELECT COUNT(*) FROM agent_network_events").fetchone()[0]
    if event_count == 0:
        events = [
            ("register", "copilot_market_intel", "{}"),
            ("register", "copilot_compliance", "{}"),
            ("heartbeat", "copilot_market_intel", "{}"),
        ]
        conn.executemany(
            "INSERT INTO agent_network_events (event_type, agent_key, detail) VALUES (?, ?, ?)",
            events,
        )

    conn.commit()
