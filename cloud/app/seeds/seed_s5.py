import json
import sqlite3


def seed_s5(conn: sqlite3.Connection) -> None:
    count_ts = conn.execute("SELECT COUNT(*) FROM training_scripts").fetchone()[0]
    count_roi = conn.execute("SELECT COUNT(*) FROM training_roi_analysis").fetchone()[0]
    if count_ts > 0 and count_roi > 0:
        return
    import json as _json
    now = "2026-05-25 10:00:00"

    if count_ts == 0:
        scripts = [
            ("ts:test-001", "竞品反击话术", "market_intel", "collab:test-001",
             "基于竞品新药上市的成功策略",
             _json.dumps([{"step":1,"action":"识别竞品弱点"},{"step":2,"action":"准备差异化证据"},{"step":3,"action":"制定标准应答"}], ensure_ascii=False),
             "mid", _json.dumps(["sales_rep","hcp_outreach"], ensure_ascii=False), 0.88),
            ("ts:test-002", "合规拜访流程", "compliance_checker", "collab:test-001",
             "标准合规拜访SOP",
             _json.dumps([{"step":1,"action":"开场合规声明"},{"step":2,"action":"信息传递"},{"step":3,"action":"合规结尾"}], ensure_ascii=False),
             "mid", _json.dumps(["sales_rep","compliance_checker"], ensure_ascii=False), 0.92),
        ]
        for script_id, name, role, collab_id, desc, steps, diff, target_roles, score in scripts:
            conn.execute(
                "INSERT INTO training_scripts (script_id, script_name, source_agent_role, "
                "source_collaboration_id, description, steps, difficulty, target_roles, "
                "score, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (script_id, name, role, collab_id, desc, steps, diff, target_roles, score, now, now))

    if count_roi == 0:
        conn.execute(
            "INSERT INTO training_roi_analysis (analysis_id, period_start, period_end, "
            "training_hours, participants, behavior_change_score, sales_impact, cost_savings, "
            "roi, metadata, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            ("roi:test-001", "2026-01-01", "2026-03-31", 120, 45, 0.72, 150000, 30000, 400.0,
             _json.dumps({"method":"simulation"}, ensure_ascii=False), now))

    new_skills = [
        ("医学事务支持", "medical_affairs", "医学证据与学术支持",
         _json.dumps(["drug","disease","compliance"], ensure_ascii=False),
         _json.dumps(["医学证据生成","学术回复"], ensure_ascii=False), 0.85, 40),
        ("市场准入分析", "market_access", "医保与招标策略",
         _json.dumps(["hospital","drug","compliance"], ensure_ascii=False),
         _json.dumps(["医保策略","招标分析"], ensure_ascii=False), 0.8, 40),
        ("患者服务支持", "patient_service", "患者教育与随访",
         _json.dumps(["disease","patient"], ensure_ascii=False),
         _json.dumps(["患者教育","随访管理"], ensure_ascii=False), 0.75, 50),
    ]
    for skill_name, agent_role, description, entity_types, capabilities, confidence, priority in new_skills:
        conn.execute(
            "INSERT OR IGNORE INTO agent_skills (skill_name, agent_role, description, "
            "entity_types, capabilities, confidence, priority, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (skill_name, agent_role, description, entity_types, capabilities, confidence, priority, now))

    conn.commit()
