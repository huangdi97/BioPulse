import sqlite3


def seed_compliance_v2(conn: sqlite3.Connection) -> None:
    """Insert preset compliance rules, audit records and training corrections if empty."""
    count = conn.execute("SELECT COUNT(*) FROM compliance_audit_records").fetchone()[0]
    if count > 0:
        return
    now = "2026-05-25 10:00:00"
    rules = [
        ("禁止绝对化用语", "prohibited_word", "根治", None),
        ("禁止疗效对比", "comparative_claim", "better than", None),
        ("必须标注不良反应", "mandatory_claim", "不良反应", None),
        ("剂量上限检查", "dosage_limit", "mg", 500.0),
    ]
    conn.executemany(
        "INSERT INTO compliance_rules (name, category, keyword, max_value, created_at) VALUES (?, ?, ?, ?, ?)",
        [(r[0], r[1], r[2], r[3], now) for r in rules],
    )
    import json as _json

    records = [
        (
            "text",
            "本品可根治糖尿病，效果远超同类产品，推荐剂量600mg/日",
            "",
            0.25,
            "critical",
            0,
            _json.dumps(
                [
                    "Prohibited word found: '根治'",
                    "Comparative claims found: better than",
                    "Dosage exceeds limit: 600 > 500.0 'mg'",
                ],
                ensure_ascii=False,
            ),
            "",
            now,
        ),
        (
            "voice",
            "该产品具有较好的疗效，但不良反应尚不明确，建议遵医嘱使用",
            "src_001",
            0.5,
            "high",
            0,
            _json.dumps(["Mandatory claim missing: '不良反应'"], ensure_ascii=False),
            "",
            "2026-05-26 09:00:00",
        ),
        (
            "text",
            "本品适用于高血压患者，常见不良反应包括头痛、头晕，请遵医嘱服用，每日剂量不超过400mg",
            "src_002",
            0.9,
            "low",
            1,
            _json.dumps([], ensure_ascii=False),
            "",
            "2026-05-26 10:00:00",
        ),
        (
            "text",
            "临床研究显示本品安全性良好，不良反应发生率低于5%，推荐剂量350mg/日",
            "src_003",
            1.0,
            "low",
            1,
            _json.dumps([], ensure_ascii=False),
            "",
            "2026-05-27 08:00:00",
        ),
        (
            "voice",
            "根据多中心临床试验数据，本品有效缓解症状，常见不良反应已标注，请在医师指导下使用",
            "src_004",
            0.95,
            "low",
            1,
            _json.dumps([], ensure_ascii=False),
            "",
            "2026-05-27 14:00:00",
        ),
    ]
    record_ids = []
    for (
        mt,
        content,
        src_id,
        score,
        risk,
        passed,
        violations,
        ai_analysis,
        ts,
    ) in records:
        cur = conn.execute(
            "INSERT INTO compliance_audit_records (message_type, content, source_id, score, risk_level, "
            "passed, violations, ai_analysis, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (mt, content, src_id, score, risk, passed, violations, ai_analysis, ts),
        )
        record_ids.append(cur.lastrowid)
    corrections = [
        (
            record_ids[0],
            "修正绝对化用语与对比声明",
            "删除'根治'和'效果远超'等绝对化和对比性表述，改为'可辅助控制血糖'",
            "content_fix",
            "high",
            "pending",
            now,
        ),
        (
            record_ids[1],
            "补充不良反应标注培训",
            "组织产品知识培训，确保所有宣传材料包含完整不良反应信息，对照合规手册第一章",
            "training",
            "high",
            "pending",
            now,
        ),
    ]
    for audit_id, title, desc, cat, sev, st, ts in corrections:
        conn.execute(
            "INSERT INTO training_corrections (audit_record_id, title, description, category, severity, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (audit_id, title, desc, cat, sev, st, ts),
        )
    conn.commit()
