import sqlite3


def seed_training_coach(conn: sqlite3.Connection) -> None:
    """Insert default training modules and attributions if tables are empty."""
    count = conn.execute("SELECT COUNT(*) FROM training_modules").fetchone()[0]
    if count > 0:
        return
    import json as _json

    now = "2026-05-25 10:00:00"
    modules = [
        (
            "合规基础",
            "compliance",
            "medium",
            "本模块介绍医药行业合规基础要求，包括《药品管理法》核心条款、广告法限制性规定、不良反应报告流程等。"
            "学员需掌握合规话术的核心要点，了解常见违规类型及修正方案。",
            _json.dumps([], ensure_ascii=False),
            0.7,
            20,
        ),
        (
            "产品入门",
            "product",
            "beginner",
            "介绍公司核心产品体系，覆盖肿瘤线、心血管线及呼吸线产品。包含产品机制、适应症、用法用量及常见不良反应概述。",
            _json.dumps(["合规基础"], ensure_ascii=False),
            0.7,
            15,
        ),
        (
            "产品深度",
            "product",
            "advanced",
            "深入解析产品关键临床研究数据、循证医学证据等级、亚组分析结果及跨适应症对比。"
            "掌握在学术拜访中运用临床证据的核心能力。",
            _json.dumps(["产品入门"], ensure_ascii=False),
            0.8,
            25,
        ),
        (
            "拜访话术",
            "sales",
            "medium",
            "医药代表拜访流程标准化训练：开场白结构→需求探询技巧→产品介绍FABE法则→异议应对模式→缔结与跟进。"
            "包含典型对话示例与分段练习。",
            _json.dumps(["产品入门"], ensure_ascii=False),
            0.7,
            20,
        ),
        (
            "竞争策略",
            "competition",
            "expert",
            "竞品情报分析与应对策略高级课程。包括竞品数据对比方法论、临床价值差异提炼、市场定位博弈、"
            "多产品线竞争组合策略及合规学术竞争框架。",
            _json.dumps(["产品深度", "拜访话术"], ensure_ascii=False),
            0.85,
            30,
        ),
    ]
    conn.executemany(
        "INSERT INTO training_modules (title, category, difficulty, content, prerequisites, "
        "passing_score, estimated_minutes, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
        [(m[0], m[1], m[2], m[3], m[4], m[5], m[6], now, now) for m in modules],
    )
    attributions = [
        (1, None, "call_rate", 45.0, 62.0, 35, now),
        (1, None, "prescription_share", 12.5, 18.2, 60, now),
        (1, None, "objection_handle_rate", 0.55, 0.72, 30, now),
    ]
    for user_id, session_id, metric, before, after, period, ts in attributions:
        change = round((after - before) / before, 4) if before else 0.0
        conn.execute(
            "INSERT INTO training_attributions (user_id, training_session_id, metric_name, "
            "metric_before, metric_after, change_pct, period_days, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (user_id, session_id, metric, before, after, change, period, ts),
        )
    conn.commit()
