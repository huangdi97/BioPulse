import sqlite3


def seed_hcp_sandbox(conn: sqlite3.Connection) -> None:
    """Insert preset HCP profiles and interactions if tables are empty."""
    count = conn.execute("SELECT COUNT(*) FROM hcp_profiles").fetchone()[0]
    if count > 0:
        return
    import json as _json

    now = "2026-05-25 10:00:00"
    profiles = [
        (
            "张明远",
            "主任医师",
            "北京协和医院",
            "肿瘤科",
            "肿瘤科",
            "北京",
            "A",
            _json.dumps(
                {"expertise": "肺癌", "years": 20, "research": "临床研究"},
                ensure_ascii=False,
            ),
            150,
            0.85,
            0.3,
        ),
        (
            "李雪梅",
            "副主任医师",
            "北京大学第一医院",
            "心血管内科",
            "心血管",
            "北京",
            "A",
            _json.dumps(
                {"expertise": "高血压", "years": 15, "style": "学术型"},
                ensure_ascii=False,
            ),
            120,
            0.75,
            0.6,
        ),
        (
            "王建国",
            "主治医师",
            "上海市胸科医院",
            "呼吸内科",
            "呼吸科",
            "上海",
            "B",
            _json.dumps(
                {"expertise": "慢阻肺", "years": 10, "style": "实践型"},
                ensure_ascii=False,
            ),
            80,
            0.45,
            0.7,
        ),
        (
            "赵丽华",
            "主任医师",
            "广州中山大学附属第一医院",
            "神经内科",
            "神经内科",
            "广州",
            "A",
            _json.dumps(
                {
                    "expertise": "癫痫",
                    "years": 18,
                    "research": "前沿",
                    "style": "权威型",
                },
                ensure_ascii=False,
            ),
            100,
            0.65,
            0.4,
        ),
        (
            "刘伟",
            "副主任医师",
            "华西医院",
            "内分泌科",
            "内分泌",
            "成都",
            "B",
            _json.dumps(
                {"expertise": "糖尿病", "years": 12, "style": "务实型"},
                ensure_ascii=False,
            ),
            90,
            0.55,
            0.5,
        ),
    ]
    conn.executemany(
        "INSERT INTO hcp_profiles (name, title, hospital, department, specialty, city, tier, "
        "traits, prescription_volume, influence_score, digital_engagement, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (
                p[0],
                p[1],
                p[2],
                p[3],
                p[4],
                p[5],
                p[6],
                p[7],
                p[8],
                p[9],
                p[10],
                now,
                now,
            )
            for p in profiles
        ],
    )
    interactions = [
        (
            1,
            "拜访",
            "介绍新产品A的临床数据",
            "表示感兴趣但需要更多对比数据",
            "积极回应，要求后续学术资料",
            "数据驱动策略",
            "2026-05-10 09:00:00",
        ),
        (
            1,
            "学术会议",
            "邀请参加省级肿瘤学术年会",
            "接受邀请并愿意做主题分享",
            "建立学术合作关系",
            "KOL合作策略",
            "2026-05-12 14:00:00",
        ),
        (
            2,
            "拜访",
            "分享心血管领域最新指南",
            "对最新指南高度关注",
            "建立了学术信任基础",
            "学术引领策略",
            "2026-05-11 10:00:00",
        ),
        (
            2,
            "随访",
            "跟进上次拜访的后续资料需求",
            "已阅读资料并提出具体问题",
            "深入讨论产品机制",
            "持续跟进策略",
            "2026-05-15 11:00:00",
        ),
        (
            3,
            "拜访",
            "首次拜访介绍公司及产品线",
            "态度平淡，时间有限",
            "仅建立初步联系",
            "标准拜访策略",
            "2026-05-08 15:00:00",
        ),
        (
            3,
            "线上会议",
            "针对呼吸科产品的线上产品说明",
            "参与较积极，提出务实问题",
            "发现临床痛点需求",
            "数字化触达策略",
            "2026-05-18 16:00:00",
        ),
        (
            4,
            "拜访",
            "介绍新药临床研究进展",
            "非常专业，追问详细数据",
            "激发了研究合作兴趣",
            "深度学术策略",
            "2026-05-09 08:00:00",
        ),
        (
            4,
            "学术会议",
            "联合举办科内小型学术沙龙",
            "主动邀请同行参加，影响广泛",
            "扩大医院影响力",
            "学术圈层策略",
            "2026-05-16 14:00:00",
        ),
        (
            5,
            "拜访",
            "讨论糖尿病管理新方案",
            "务实，关注成本效益比",
            "达成初步试用意向",
            "疗效经济性策略",
            "2026-05-13 10:00:00",
        ),
    ]
    conn.executemany(
        "INSERT INTO hcp_interactions (hcp_id, interaction_type, content, response, outcome, "
        "strategy_used, conducted_at, created_at) VALUES (?,?,?,?,?,?,?,?)",
        [(i[0], i[1], i[2], i[3], i[4], i[5], i[6], now) for i in interactions],
    )
    conn.commit()
