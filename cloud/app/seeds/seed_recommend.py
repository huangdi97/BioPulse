import sqlite3


def seed_recommend(conn: sqlite3.Connection) -> None:
    """Insert default recommendation engine seed data if empty."""
    count = conn.execute("SELECT COUNT(*) FROM user_profiles").fetchone()[0]
    if count > 0:
        return
    now = "2026-05-25 10:00:00"

    profiles = [
        (1, "rep", "肿瘤科", "senior", '["临床数据","市场报告"]', '["肿瘤","新药"]'),
        (2, "manager", "心血管", "mid", '["战略分析","竞品情报"]', '["心血管","管理"]'),
        (3, "analyst", "全科", "junior", '["培训材料","诊疗规范"]', '["全科","学习"]'),
    ]
    for user_id, persona_type, specialization, exp_lvl, content_types, tags in profiles:
        conn.execute(
            "INSERT OR REPLACE INTO user_profiles (user_id, persona_type, specialization, "
            "experience_level, preferred_content_types, custom_tags, created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (user_id, persona_type, specialization, exp_lvl, content_types, tags, now),
        )

    behaviors = [
        (1, "view", "content", "市场洞察报告", '{"duration":120}', 120, now),
        (1, "search", "content", "新药A", '{"query":"新药A 临床"}', 30, now),
        (2, "view", "content", "竞品分析", '{"duration":90}', 90, now),
        (3, "create", "content", "患者分析", '{"doc_type":"报告"}', 180, now),
        (2, "search", "content", "2型糖尿病", '{"query":"2型糖尿病 诊疗"}', 45, now),
    ]
    for uid, action, target_type, target_id, metadata, dur, ts in behaviors:
        conn.execute(
            "INSERT INTO user_behaviors (user_id, action_type, target_type, target_id, "
            "metadata, duration_seconds, created_at) VALUES (?,?,?,?,?,?,?)",
            (uid, action, target_type, target_id, metadata, dur, ts),
        )

    recs = [
        (
            1,
            "content",
            "新药A最新临床数据",
            "基于浏览行为和兴趣标签推荐",
            0.95,
            "tag-match",
            0,
            0,
            now,
        ),
        (
            2,
            "strategy",
            "竞品B对比策略",
            "基于竞品分析行为推荐",
            0.85,
            "behavior-match",
            0,
            0,
            now,
        ),
        (
            3,
            "training",
            "糖尿病诊疗规范",
            "基于分析角色推荐",
            0.75,
            "role-match",
            1,
            0,
            now,
        ),
    ]
    for uid, rec_type, title, reason, score, strategy, clk, dis, ts in recs:
        conn.execute(
            "INSERT INTO recommendations (user_id, rec_type, rec_title, rec_reason, "
            "score, strategy_name, clicked, dismissed, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (uid, rec_type, title, reason, score, strategy, clk, dis, ts),
        )

    conn.commit()
