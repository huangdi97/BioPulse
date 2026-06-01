import sqlite3


def seed_collaboration(conn: sqlite3.Connection) -> None:
    """Insert default agent skills and collaboration sessions if tables are empty."""
    count = conn.execute("SELECT COUNT(*) FROM agent_skills").fetchone()[0]
    if count > 0:
        return
    import json as _json

    now = "2026-05-25 10:00:00"
    now_plus = "2026-05-25 11:00:00"

    skills = [
        (
            "市场情报分析",
            "market_intel",
            "分析市场情报数据，追踪竞品动态，评估市场影响",
            _json.dumps(["drug", "disease"], ensure_ascii=False),
            _json.dumps(["竞品分析", "市场情报"], ensure_ascii=False),
            0.85,
            50,
        ),
        (
            "HCP分析",
            "hcp_outreach",
            "分析HCP档案，制定拜访策略和数字触达方案",
            _json.dumps(["hcp"], ensure_ascii=False),
            _json.dumps(["HCP档案分析", "拜访策略"], ensure_ascii=False),
            0.8,
            50,
        ),
        (
            "合规检查",
            "compliance_checker",
            "审核推广材料和互动内容，进行合规风险检查",
            _json.dumps(["compliance"], ensure_ascii=False),
            _json.dumps(["合规检查", "风险评估"], ensure_ascii=False),
            0.9,
            30,
        ),
    ]
    for (
        skill_name,
        agent_role,
        description,
        entity_types,
        capabilities,
        confidence,
        priority,
    ) in skills:
        conn.execute(
            "INSERT INTO agent_skills (skill_name, agent_role, description, entity_types, "
            "capabilities, confidence, priority, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (
                skill_name,
                agent_role,
                description,
                entity_types,
                capabilities,
                confidence,
                priority,
                now,
            ),
        )

    sessions = [
        (
            "collab:test-001",
            "竞品新药上市影响分析",
            "",
            "",
            "completed",
            _json.dumps(
                ["market_intel", "compliance_checker", "hcp_outreach"],
                ensure_ascii=False,
            ),
            "semantic",
            3,
            3,
            now,
            now_plus,
            "全流程完成：情报分析→合规审查→HCP策略输出",
        ),
        (
            "collab:test-002",
            "糖尿病领域KOL图谱构建",
            "",
            "",
            "active",
            _json.dumps(["hcp_outreach", "market_intel"], ensure_ascii=False),
            "semantic",
            2,
            1,
            now,
            None,
            "",
        ),
    ]
    for (
        session_id,
        task,
        src_eid,
        src_role,
        status,
        agents,
        strategy,
        total,
        comp,
        started,
        completed,
        result,
    ) in sessions:
        conn.execute(
            "INSERT INTO collaboration_sessions (session_id, task_description, source_entity_id, "
            "source_agent_role, status, involved_agents, routing_strategy, total_steps, "
            "completed_steps, started_at, completed_at, result_summary) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                session_id,
                task,
                src_eid,
                src_role,
                status,
                agents,
                strategy,
                total,
                comp,
                started,
                completed,
                result,
            ),
        )

    steps = [
        (
            "collab:test-001",
            1,
            "market_intel",
            "process",
            "分析竞品新药对市场的影响",
            "竞品新药在III期临床中ORR达58%，预计6个月内冲击我方15%-20%市场份额",
            "",
            "completed",
            now,
            now_plus,
            120,
            _json.dumps({"confidence": 0.85, "risk_level": "high"}, ensure_ascii=False),
        ),
        (
            "collab:test-001",
            2,
            "compliance_checker",
            "process",
            "审查竞品对比推广材料合规性",
            "发现宣传材料中对比性表述需修正，已生成合规话术建议",
            "",
            "completed",
            now_plus,
            "2026-05-25 11:30:00",
            90,
            _json.dumps(
                {"violations_found": 2, "risk_level": "medium"}, ensure_ascii=False
            ),
        ),
        (
            "collab:test-001",
            3,
            "hcp_outreach",
            "process",
            "基于情报和合规结果制定HCP拜访策略",
            "已制定面向肿瘤科KOL的差异化拜访方案，包含核心信息要点",
            "",
            "completed",
            "2026-05-25 11:30:00",
            "2026-05-25 12:00:00",
            60,
            _json.dumps({"target_hcps": 15, "priority": "high"}, ensure_ascii=False),
        ),
        (
            "collab:test-002",
            1,
            "hcp_outreach",
            "process",
            "从HCP库中识别糖尿病领域关键KOL",
            "已筛选出15位糖尿病领域高影响力HCP，按tier和影响力评分排序",
            "",
            "completed",
            now,
            now_plus,
            45,
            _json.dumps(
                {"hcp_count": 15, "tier_distribution": {"A": 5, "B": 7, "C": 3}},
                ensure_ascii=False,
            ),
        ),
        (
            "collab:test-002",
            2,
            "market_intel",
            "process",
            "为目标HCP匹配最新的市场情报和学术动态",
            "",
            "",
            "pending",
            None,
            None,
            0,
            "{}",
        ),
    ]
    for (
        sid,
        order,
        role,
        action,
        inp,
        out,
        eid,
        status,
        started,
        completed,
        dur,
        meta,
    ) in steps:
        conn.execute(
            "INSERT INTO collaboration_steps (session_id, step_order, agent_role, action_type, "
            "input_summary, output_summary, entity_id, status, started_at, completed_at, "
            "duration_seconds, metadata) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                sid,
                order,
                role,
                action,
                inp,
                out,
                eid,
                status,
                started,
                completed,
                dur,
                meta,
            ),
        )
    conn.commit()
