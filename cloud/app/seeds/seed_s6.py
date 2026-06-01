def seed_s6(conn):
    import json as _json

    now = "2026-05-25 10:00:00"
    rows = conn.execute("SELECT COUNT(*) FROM effect_metrics").fetchone()[0]
    if rows > 0:
        conn.commit()
        return
    conn.execute(
        "INSERT OR IGNORE INTO effect_metrics (metric_id, agent_role, metric_type, metric_value, metric_unit, source_table, source_row_id, period_start, period_end, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            "em:test-001",
            "market_intel",
            "time_saved",
            120,
            "hours/week",
            "agent_skills",
            "skill-001",
            "2026-01-01",
            "2026-03-31",
            now,
        ),
    )
    conn.execute(
        "INSERT OR IGNORE INTO benchmark_reports (report_id, report_name, report_type, summary, metrics, period, created_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (
            "bm:test-001",
            "2026Q1行业对标",
            "sales",
            "2026Q1行业对标报告",
            _json.dumps(
                {"avg_visit_freq": 3.5, "conversion_rate": 0.28}, ensure_ascii=False
            ),
            "2026Q1",
            now,
        ),
    )
    conn.execute(
        "INSERT OR IGNORE INTO agent_marketplace (item_id, item_name, description, agent_config, category, price_model, rating, download_count, enabled, publisher, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            "mp:test-001",
            "市场情报Agent",
            "市场情报自动采集",
            _json.dumps({"agent_role": "market_intel"}, ensure_ascii=False),
            "市场情报",
            "free",
            4.5,
            120,
            1,
            "系统",
            now,
        ),
    )
    conn.execute(
        "INSERT OR IGNORE INTO agent_marketplace (item_id, item_name, description, agent_config, category, price_model, rating, download_count, enabled, publisher, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            "mp:test-002",
            "合规检查Agent",
            "自动合规审查",
            _json.dumps({"agent_role": "compliance"}, ensure_ascii=False),
            "合规",
            "subscription",
            4.8,
            85,
            1,
            "系统",
            now,
        ),
    )
    conn.execute(
        "INSERT OR IGNORE INTO supply_chain_items (item_id, item_name, sku, category, current_stock, min_stock, max_stock, unit_price, supplier, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            "sc:test-001",
            "骨科植入物A",
            "IMP-001",
            "implant",
            85,
            20,
            200,
            3500,
            "强生",
            now,
        ),
    )
    conn.execute(
        "INSERT OR IGNORE INTO supply_chain_items (item_id, item_name, sku, category, current_stock, min_stock, max_stock, unit_price, supplier, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            "sc:test-002",
            "缝合线B",
            "SUT-002",
            "consumable",
            200,
            50,
            500,
            120,
            "威高",
            now,
        ),
    )
    conn.execute(
        "INSERT OR IGNORE INTO sensor_sessions (session_id, session_name, event_type, location, start_time, end_time, created_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (
            "ss:test-001",
            "2026Q1全国肿瘤峰会",
            "academic_meeting",
            "上海",
            "2026-03-15 09:00:00",
            "2026-03-17 18:00:00",
            now,
        ),
    )
    conn.commit()
