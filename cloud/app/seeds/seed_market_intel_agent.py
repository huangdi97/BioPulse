import sqlite3


def seed_market_intel_agent(conn: sqlite3.Connection) -> None:
    """Insert market intel analyst agent template and instance."""
    count = conn.execute("SELECT COUNT(*) FROM agent_role_templates WHERE template_key='market_intel_analyst'").fetchone()[0]
    if count > 0:
        return
    conn.execute(
        "INSERT OR IGNORE INTO agent_role_templates (template_key, name, domain, capabilities, default_config) VALUES (?, ?, ?, ?, ?)",
        (
            "market_intel_analyst",
            "市场情报分析师Agent",
            "intel",
            '["market_analyze","competitor_tracking","trend_forecast","pubmed_search","causal_attribution"]',
            '{"auto_register":true}',
        ),
    )
    conn.execute(
        "INSERT OR IGNORE INTO agent_instances (instance_key, template_key, bind_to_end, status) VALUES (?, ?, ?, ?)",
        ("market_intel_analyst_01", "market_intel_analyst", "cloud", "running"),
    )
    conn.commit()
