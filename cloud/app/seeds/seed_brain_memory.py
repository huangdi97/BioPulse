"""种子数据：预设情景记忆（MDT辩论/决策/HCP模拟/合规检查/培训）。"""

import sqlite3


def seed_brain_memory(conn: sqlite3.Connection) -> None:
    """Insert preset episodic memories (MDT debate/decision/HCP simulation/compliance check/training) if table is empty."""
    count = conn.execute("SELECT COUNT(*) FROM episodic_memory").fetchone()[0]
    if count > 0:
        return
    import json as _json

    now = "2026-05-25 10:00:00"
    episodes = [
        (
            "mdt_debate",
            "MDT辩论: 集采政策应对策略辩论",
            "多方专家围绕集采政策展开激烈辩论，情报分析师提供市场数据，策略规划师提出差异化定位方案，"
            "销售代表关注执行可行性，复盘分析师以历史案例为据。最终达成共识：加速创新药管线布局，"
            "通过学术推广建立品牌护城河。",
            _json.dumps(
                {"session_id": 1, "participants": 4, "rounds": 1, "topic": "集采政策"},
                ensure_ascii=False,
            ),
            "constructive",
            0.70,
            0.80,
            _json.dumps(
                ["情报分析师", "策略规划师", "销售代表", "复盘分析师"],
                ensure_ascii=False,
            ),
            "mdt_session",
            1,
        ),
        (
            "decision",
            "决策: 竞品A新药上市应对策略",
            "基于竞品A新药获NMPA批准上市的情报，团队使用SOAP框架分析：竞品III期临床ORR达58%，"
            "我方市场份额从32%降至28%。评估后制定学术反制策略，联合KOL开展安全性与全适应症巡讲，"
            "加速新适应症临床数据发布。",
            _json.dumps(
                {"template_id": 1, "priority": "high", "status": "draft"},
                ensure_ascii=False,
            ),
            "draft",
            -0.15,
            0.65,
            _json.dumps(["情报分析师", "策略规划师"], ensure_ascii=False),
            "soap_decision",
            1,
        ),
        (
            "hcp_simulation",
            "HCP模拟: 拜访张明远主任探讨新产品临床数据",
            "模拟拜访北京协和医院肿瘤科张明远主任。采用数据驱动策略，介绍新产品A的临床数据。"
            "王主任表示感兴趣但需要更多对比数据，要求后续提供学术资料。成功建立初步学术合作关系，"
            "预约两周后随访。",
            _json.dumps(
                {"hcp_id": 1, "interaction_type": "拜访", "strategy": "数据驱动策略"},
                ensure_ascii=False,
            ),
            "积极回应，要求后续学术资料",
            0.35,
            0.50,
            _json.dumps(["销售代表"], ensure_ascii=False),
            "hcp_interaction",
            1,
        ),
        (
            "compliance_check",
            "合规检查: 推广材料绝对化用语审查",
            "对近期推广材料进行合规审计，发现3份材料含绝对化用语（如'根治'），2份含疗效对比声明。"
            "违规率较上季度上升2%。根源为竞品压力下销售团队追求差异化表述。已启动整改：召回问题材料，"
            "全员合规培训，建立双人审核机制。",
            _json.dumps(
                {
                    "record_ids": [1, 2],
                    "violations": ["绝对化用语", "疗效对比"],
                    "risk_level": "high",
                },
                ensure_ascii=False,
            ),
            "部分违规，已启动整改",
            -0.45,
            0.70,
            _json.dumps(["合规专员"], ensure_ascii=False),
            "compliance_audit",
            1,
        ),
        (
            "training",
            "培训: 合规基础培训圆满完成",
            "组织全体销售代表参加合规基础培训，覆盖《药品管理法》核心条款、广告法限制性规定、"
            "不良反应报告流程等核心内容。学员通过率100%，平均得分92分。培训后开展了情景模拟考核，"
            "显著提升了团队合规意识和话术运用能力。",
            _json.dumps(
                {"module_id": 1, "category": "compliance", "passing_score": 0.7},
                ensure_ascii=False,
            ),
            "全体通过，平均92分",
            0.80,
            0.40,
            _json.dumps(["培训教练"], ensure_ascii=False),
            "training_module",
            1,
        ),
    ]
    for (
        et,
        title,
        desc,
        ctx,
        outcome,
        valence,
        intensity,
        agents,
        rtype,
        rid,
    ) in episodes:
        conn.execute(
            "INSERT INTO episodic_memory (event_type, title, description, context, "
            "outcome, valence, intensity, involved_agents, related_entity_type, "
            "related_entity_id, created_by, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                et,
                title,
                desc,
                ctx,
                outcome,
                valence,
                intensity,
                agents,
                rtype,
                rid,
                "1",
                now,
            ),
        )
    conn.commit()
