import sqlite3


def seed_event_bus(conn: sqlite3.Connection) -> None:
    """Insert default event bus definitions, messages and delivery logs if tables are empty."""
    count = conn.execute("SELECT COUNT(*) FROM event_bus_definitions").fetchone()[0]
    if count > 0:
        return
    import json as _json

    now = "2026-05-25 10:00:00"

    definitions = [
        (
            "compliance.alert",
            "合规告警",
            "合规审查触发告警，推送至销售辅助与助理端",
            "cloud",
            _json.dumps(["sales-coach", "assistant"], ensure_ascii=False),
            _json.dumps(
                {"alert_level": "string", "violations": "array"}, ensure_ascii=False
            ),
            50,
        ),
        (
            "recommendation.ready",
            "推荐就绪",
            "推荐引擎生成新推荐，推送至销售助理与机会管理端",
            "cloud",
            _json.dumps(["sales-assistant", "opportunity"], ensure_ascii=False),
            _json.dumps(
                {"content_type": "string", "score": "number"}, ensure_ascii=False
            ),
            100,
        ),
        (
            "identity.updated",
            "身份更新",
            "身份信息变更，同步至云端与助理端",
            "cloud",
            _json.dumps(["cloud", "assistant"], ensure_ascii=False),
            _json.dumps(
                {"did": "string", "updated_fields": "array"}, ensure_ascii=False
            ),
            80,
        ),
        (
            "surgery.created",
            "手术创建",
            "手术排程创建，通知助理与云服务端",
            "sales-coach",
            _json.dumps(["assistant", "cloud"], ensure_ascii=False),
            _json.dumps(
                {"surgery_id": "string", "hcp_id": "string"}, ensure_ascii=False
            ),
            100,
        ),
        (
            "opportunity.won",
            "商机赢得",
            "商机成交通知，同步至云端与销售助理端",
            "opportunity",
            _json.dumps(["cloud", "sales-assistant"], ensure_ascii=False),
            _json.dumps(
                {"opportunity_id": "string", "value": "number"}, ensure_ascii=False
            ),
            120,
        ),
        (
            "system.health",
            "系统健康",
            "系统健康检查，广播至全端",
            "cloud",
            _json.dumps([], ensure_ascii=False),
            _json.dumps({"status": "string", "uptime": "number"}, ensure_ascii=False),
            10,
        ),
    ]
    conn.executemany(
        "INSERT INTO event_bus_definitions (event_type, display_name, description, "
        "source_end, target_ends, schema_template, priority, created_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        [(*d, now) for d in definitions],
    )

    messages = [
        (
            "evt:test-001",
            "compliance.alert",
            "cloud",
            "content",
            "content-42",
            _json.dumps(
                {"alert_level": "high", "violations": ["absolute_word"]},
                ensure_ascii=False,
            ),
            "",
            100,
            "pending",
            now,
        ),
        (
            "evt:test-002",
            "recommendation.ready",
            "cloud",
            "content",
            "content-99",
            _json.dumps(
                {"content_type": "strategy", "score": 0.92}, ensure_ascii=False
            ),
            "",
            100,
            "delivered",
            now,
        ),
        (
            "evt:test-003",
            "opportunity.won",
            "opportunity",
            "opportunity",
            "opp-005",
            _json.dumps(
                {"opportunity_id": "opp-005", "value": 150000}, ensure_ascii=False
            ),
            "",
            120,
            "pending",
            now,
        ),
    ]
    for (
        msg_id,
        evt_type,
        src_end,
        src_etype,
        src_eid,
        payload,
        corr_id,
        pri,
        status,
        ts,
    ) in messages:
        conn.execute(
            "INSERT INTO event_bus_messages (message_id, event_type, source_end, "
            "source_entity_type, source_entity_id, payload, correlation_id, priority, "
            "status, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                msg_id,
                evt_type,
                src_end,
                src_etype,
                src_eid,
                payload,
                corr_id,
                pri,
                status,
                ts,
            ),
        )

    logs = [
        ("evt:test-001", "sales-coach", "delivered", 1, "OK: 200", 45, ""),
        ("evt:test-001", "assistant", "pending", 1, "", 0, "endpoint unreachable"),
        ("evt:test-002", "sales-assistant", "delivered", 1, "OK: 200", 32, ""),
        ("evt:test-002", "opportunity", "delivered", 1, "OK: 200", 28, ""),
        ("evt:test-003", "cloud", "pending", 1, "", 0, "target busy"),
        ("evt:test-003", "sales-assistant", "pending", 1, "", 0, "timeout"),
    ]
    conn.executemany(
        "INSERT INTO event_delivery_log (message_id, target_end, delivery_status, attempt, "
        "response_summary, duration_ms, error_message, created_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        [(l[0], l[1], l[2], l[3], l[4], l[5], l[6], now) for l in logs],
    )
    conn.commit()
