import json
import sqlite3


def seed_agent_data(conn: sqlite3.Connection) -> None:
    """Insert preset agent roles and pipeline if tables are empty."""
    count = conn.execute("SELECT COUNT(*) FROM agent_roles").fetchone()[0]
    if count > 0:
        return
    now = "2026-05-25 10:00:00"
    roles = [
        ("情报分析师Agent", "analyst", "你是一名医药行业情报分析师，擅长分析市场情报数据。"
         "请根据输入的情报信息，提炼关键洞察，评估商业影响，给出建议行动。"
         "以JSON格式输出：{\"key_insights\":[...],\"impact_assessment\":\"...\",\"recommended_actions\":[...]}。",
         "分析医药市场情报，提炼关键洞察", 0.3),
        ("策略规划Agent", "strategist", "你是一名医药销售策略规划师。"
         "基于市场情报分析和客户数据，制定拜访策略和优先级排序。"
         "输出行动计划和关键论点，以JSON格式：{\"priority_clients\":[...],\"key_arguments\":[...],\"action_plan\":\"...\"}。",
         "基于情报制定拜访策略和行动计划", 0.5),
        ("销售代表Agent", "sales_rep", "你是一名经验丰富的医药销售代表。"
         "根据策略规划，生成具体的客户拜访话术。包括：开场白、产品核心信息要点、异议应对方案、跟进计划。"
         "输出格式：{\"opening\":\"...\",\"key_messages\":[...],\"objection_handling\":[...],\"follow_up\":\"...\"}。",
         "根据策略生成客户拜访话术和建议", 0.7),
        ("复盘分析师Agent", "coach", "你是一名销售教练（复盘分析师）。"
         "分析销售拜访记录或执行结果，识别成功模式和可复制经验，给出改进建议。"
         "输出格式：{\"success_patterns\":[...],\"improvement_areas\":[...],\"specific_recommendations\":[...]}。",
         "分析销售记录，给出改进建议", 0.5),
    ]
    conn.executemany(
        "INSERT INTO agent_roles (name, role_type, system_prompt, description, temperature, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(r[0], r[1], r[2], r[3], r[4], now, now) for r in roles],
    )
    pipeline_id = conn.execute(
        "INSERT INTO agent_pipelines (name, description, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("情报驱动拜访策略", "从市场情报分析开始，制定拜访策略，生成销售话术", now, now),
    ).lastrowid
    steps_data = [
        (pipeline_id, 1, 1, '{"user_input":"$request"}', ""),
        (pipeline_id, 2, 2, '{"context":"previous_output"}', ""),
        (pipeline_id, 3, 3, '{"strategy":"previous_output","user_input":"$request"}', ""),
    ]
    conn.executemany(
        "INSERT INTO pipeline_steps (pipeline_id, step_order, agent_role_id, input_mapping, custom_prompt_override) "
        "VALUES (?, ?, ?, ?, ?)",
        steps_data,
    )
    conn.commit()
