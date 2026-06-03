import sqlite3


def seed_soap_decision(conn: sqlite3.Connection) -> None:
    """Insert default SOAP templates, decisions and async MDT opinions if tables are empty."""
    count = conn.execute("SELECT COUNT(*) FROM soap_templates").fetchone()[0]
    if count > 0:
        return
    import json as _json

    now = "2026-05-25 10:00:00"
    templates = [
        (
            "通用SOAP模板",
            "general",
            _json.dumps(
                {
                    "sections": ["Subjective", "Objective", "Assessment", "Plan"],
                    "fields": {
                        "Subjective": "主诉与主观信息",
                        "Objective": "客观数据与检查结果",
                        "Assessment": "评估与诊断分析",
                        "Plan": "行动计划与策略",
                    },
                },
                ensure_ascii=False,
            ),
        ),
        (
            "产品策略SOAP模板",
            "product_strategy",
            _json.dumps(
                {
                    "sections": ["Subjective", "Objective", "Assessment", "Plan"],
                    "fields": {
                        "Subjective": "客户反馈与市场感知",
                        "Objective": "销量数据与竞品动态",
                        "Assessment": "产品定位与差异化分析",
                        "Plan": "推广策略与资源分配",
                    },
                },
                ensure_ascii=False,
            ),
        ),
        (
            "合规评估SOAP模板",
            "compliance",
            _json.dumps(
                {
                    "sections": ["Subjective", "Objective", "Assessment", "Plan"],
                    "fields": {
                        "Subjective": "合规风险感知",
                        "Objective": "审计数据与违规记录",
                        "Assessment": "风险等级与影响评估",
                        "Plan": "整改方案与培训计划",
                    },
                },
                ensure_ascii=False,
            ),
        ),
    ]
    conn.executemany(
        "INSERT INTO soap_templates (name, category, structure, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        [(t[0], t[1], t[2], now, now) for t in templates],
    )
    decisions = [
        (
            1,
            "竞品A新药上市应对策略决策",
            "团队反馈客户询问竞品A新药数据频繁，市场部感知到竞争压力增大",
            "竞品A新药III期临床ORR 58%，已获NMPA批准；我方产品市场份额从32%降至28%，近3个月下降4个百分点",
            "竞品A在疗效数据上具有明显优势，但适应症覆盖范围较窄；我方产品安全性数据更优，且适应症更广。"
            "短期内面临15%-20%市场冲击，需在2个月内启动学术反制策略。",
            "1. 整理我方产品安全性对比数据并制作学术推广材料；2. 联合3家KOL开展安全性与全适应症优势巡讲；"
            "3. 加速新适应症临床数据发布节奏；4. 组建竞品应对专项团队，周度复盘市场变化",
            "draft",
            "high",
            _json.dumps(["竞品分析", "肺癌", "市场策略", "学术推广"], ensure_ascii=False),
        ),
        (
            2,
            "合规推广材料修订决策",
            "内部抽查发现部分推广材料存在对比性表述，合规团队发出风险预警",
            "近3个月合规审计：5份材料违规，其中3份含绝对化用语、2份含疗效对比；违规率较上季度上升2%",
            "主要问题集中在竞品对比部分表述不当，风险等级为中等。根源在于竞品压力下销售团队追求差异化表述。"
            "虽暂未收到监管处罚，但需立即整顿避免系统性风险。",
            "1. 召回并修订全部已发出存在问题的材料；2. 全团队合规培训（48小时内完成）；"
            "3. 建立发布前双人审核机制；4. 月度合规抽查覆盖率达到100%",
            "draft",
            "medium",
            _json.dumps(["合规", "推广材料", "风险控制", "培训"], ensure_ascii=False),
        ),
    ]
    decision_ids = []
    for tid, title, subj, obj, assess, plan, status, pri, tags in decisions:
        cur = conn.execute(
            "INSERT INTO soap_decisions (template_id, title, subjective, objective, assessment, "
            "plan, status, priority, tags, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (tid, title, subj, obj, assess, plan, status, pri, tags, now, now),
        )
        decision_ids.append(cur.lastrowid)
    opinions = [
        (
            decision_ids[0],
            1,
            "情报分析师",
            "根据最新情报，竞品A新药获批后已在5家头部三甲医院完成准入。"
            "其销售团队规模扩张计划显示将新增200名代表，覆盖全国主要城市。建议我方立即启动竞品数据对比分析，"
            "重点挖掘竞品在安全性、药物相互作用方面的弱点。支持数据已上传附件。",
            _json.dumps({"竞争情报": {"竞品准入": 5, "销售扩张": "200人"}}, ensure_ascii=False),
            "supportive",
            0.85,
            _json.dumps(["竞品情报摘要.pdf", "市场分布图.png"], ensure_ascii=False),
        ),
        (
            decision_ids[0],
            2,
            "策略规划师",
            "基于竞品优势在疗效但弱点在适应症范围的判断，建议采取差异化定位策略。"
            "我方应强调'更广泛适应症覆盖+更好安全性记录'作为核心信息，避免与竞品在疗效数据上直接对比。"
            "建议分配60%资源用于学术推广，30%用于数字化触达，10%用于KOL维护。",
            _json.dumps(
                {"资源分配": {"学术推广": 0.6, "数字化": 0.3, "KOL": 0.1}},
                ensure_ascii=False,
            ),
            "supportive",
            0.78,
            _json.dumps(["差异化策略方案.pdf"], ensure_ascii=False),
        ),
        (
            decision_ids[0],
            3,
            "销售总监",
            "从落地角度看，差异化策略需要销售团队重新学习话术，需要2-3周培训周期。"
            "同时竞品也在加速推广，时间窗口紧迫。建议简化核心信息到3个关键论点，制作便携式'话术卡片'，"
            "先在一线团队试点2周再全面推广。",
            "",
            "neutral",
            0.65,
            _json.dumps([], ensure_ascii=False),
        ),
        (
            decision_ids[1],
            1,
            "合规专员",
            "审计发现的违规问题集中在与竞品相关的陈述中。根源是竞品压力下销售团队在推广中"
            "缺乏足够合规支持材料。建议一方面加强合规培训，更重要的是提供'合规的差异化话术模板'，"
            "让团队在不违规的前提下有效传递产品优势。",
            _json.dumps(
                {"违规分类": {"绝对化用语": 3, "疗效对比": 2}, "根本原因": "竞品压力"},
                ensure_ascii=False,
            ),
            "supportive",
            0.92,
            _json.dumps(["合规审计报告Q2.pdf", "违规材料清单.xlsx"], ensure_ascii=False),
        ),
    ]
    for did, cid, crole, opinion, sdata, stance, conf, att in opinions:
        conn.execute(
            "INSERT INTO async_mdt_opinions (decision_id, contributor_id, contributor_role, "
            "opinion, supporting_data, stance, confidence, attachments, is_final, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,1,?,?)",
            (did, cid, crole, opinion, sdata, stance, conf, att, now, now),
        )
    conn.commit()
