import json
import sqlite3
import os
from datetime import datetime, timezone
from typing import List

_CLOUD_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "cloud.db",
)


def _get_cloud_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_CLOUD_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _read_kg_entities(entity_types: List[str]) -> List[dict]:
    conn = _get_cloud_conn()
    try:
        placeholders = ",".join("?" for _ in entity_types)
        rows = conn.execute(
            f"SELECT entity_id, entity_type, name, properties FROM kg_entities "
            f"WHERE entity_type IN ({placeholders}) AND status = 'active'", entity_types,
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


_S = {"communication": 0.4, "product_knowledge": 0.2, "compliance": 0.2, "objection_handling": 0.2}
_S2 = {"communication": 0.3, "product_knowledge": 0.3, "compliance": 0.2, "objection_handling": 0.2}
_S3 = {"product_knowledge": 0.35, "communication": 0.3, "compliance": 0.2, "objection_handling": 0.15}
_S4 = {"product_knowledge": 0.4, "communication": 0.25, "compliance": 0.25, "objection_handling": 0.1}
_S5 = {"product_knowledge": 0.35, "objection_handling": 0.3, "compliance": 0.25, "communication": 0.1}
_S6 = {"product_knowledge": 0.35, "communication": 0.25, "compliance": 0.2, "objection_handling": 0.2}
_S7 = {"objection_handling": 0.35, "product_knowledge": 0.25, "communication": 0.2, "compliance": 0.2}
_S8 = {"product_knowledge": 0.35, "objection_handling": 0.3, "compliance": 0.2, "communication": 0.15}
_S9 = {"product_knowledge": 0.3, "objection_handling": 0.3, "compliance": 0.25, "communication": 0.15}
_S10 = {"objection_handling": 0.35, "product_knowledge": 0.25, "compliance": 0.25, "communication": 0.15}
_S11 = {"compliance": 0.5, "communication": 0.25, "product_knowledge": 0.25, "objection_handling": 0.0}
_S12 = {"compliance": 0.5, "communication": 0.3, "objection_handling": 0.2, "product_knowledge": 0.0}
_S13 = {"compliance": 0.5, "product_knowledge": 0.15, "communication": 0.2, "objection_handling": 0.15}
_S14 = {"communication": 0.3, "product_knowledge": 0.25, "objection_handling": 0.25, "compliance": 0.2}
_S15 = {"communication": 0.3, "product_knowledge": 0.3, "compliance": 0.3, "objection_handling": 0.1}
_S16 = {"compliance": 0.35, "communication": 0.3, "objection_handling": 0.2, "product_knowledge": 0.15}
_S17 = {"product_knowledge": 0.3, "communication": 0.3, "compliance": 0.2, "objection_handling": 0.2}
_S18 = {"product_knowledge": 0.35, "communication": 0.3, "compliance": 0.2, "objection_handling": 0.15}
_S19 = {"product_knowledge": 0.35, "communication": 0.3, "compliance": 0.25, "objection_handling": 0.1}
_S20 = {"product_knowledge": 0.3, "compliance": 0.3, "communication": 0.25, "objection_handling": 0.15}
_S21 = {"product_knowledge": 0.3, "communication": 0.3, "compliance": 0.25, "objection_handling": 0.15}

FIXED_SCENARIOS = [
    dict(title="初次拜访医生", role_setting="你是一名医药代表，首次拜访一位三甲医院的心内科主任医师",
         goal="建立良好的第一印象，获取医生初步信任", difficulty="easy", category="opening",
         content="你第一次拜访这位医生，需要简洁自我介绍并说明拜访目的。医生对医药代表持保留态度。",
         tips="注意开场礼貌，简明扼要，不要急于介绍产品细节，留好后续拜访空间。",
         scoring_weights=_S, compliance_points=["禁止夸大产品疗效", "禁止贬低竞品", "禁止未经批准的适应症宣传"]),
    dict(title="常规拜访跟进", role_setting="你是一名医药代表，例行拜访一位已建立联系的社区卫生中心主任",
         goal="更新产品信息，了解医生近期用药反馈", difficulty="easy", category="opening",
         content="这是你第三次拜访这位医生，他/她已经处方过你的产品。你需要了解使用反馈并更新最新临床数据。",
         tips="保持专业和谦逊，主动询问使用体验，针对性解答疑问。",
         scoring_weights=_S2, compliance_points=["禁止诱导处方", "需客观陈述数据", "禁止利益输送暗示"]),
    dict(title="学术拜访", role_setting="你是一名医学信息顾问，拜访一家省级医院科室主任进行学术交流",
         goal="通过学术内容建立专业形象，推动学术共识", difficulty="medium", category="opening",
         content="你携带最新临床研究摘要拜访科室主任，希望就某一治疗领域的最新进展进行学术探讨。",
         tips="以学术讨论为导向，引用权威文献，避免过度商业化的表达。",
         scoring_weights=_S3, compliance_points=["学术引用需有据可查", "禁止虚假数据", "禁止诱导处方"]),
    # 产品介绍类（3种）
    dict(title="产品核心信息传递", role_setting="你是一名医药代表，向一位内分泌科医生介绍一款新型降糖药物",
         goal="准确传递产品的核心临床数据和适应症信息", difficulty="medium", category="product_intro",
         content="医生对这类新药了解有限，请你从药物机制、临床疗效、安全性三个方面进行介绍。",
         tips="重点突出循证医学证据，使用客观数据，避免绝对化表述。",
         scoring_weights=_S4, compliance_points=["禁止超出说明书的适应症宣传", "引用数据需标注来源", "禁止与其他产品做不当比较"]),
    dict(title="竞品对比分析", role_setting="你是一名医药代表，医生要求你比较你的产品和市场上同类竞品的差异",
         goal="客观介绍产品差异化优势，同时尊重竞品", difficulty="hard", category="product_intro",
         content="医生同时在使用竞品，直接要求你说明你的产品相比竞品有什么优势。",
         tips="客观陈述差异化特点，不要直接贬低竞品，以临床数据为支撑。",
         scoring_weights=_S5, compliance_points=["禁止贬低竞品", "禁止无依据的功效比较", "需基于头对头研究或真实世界证据"]),
    dict(title="真实世界数据解读", role_setting="你是一名医学顾问，向一位肿瘤科医生展示产品的真实世界研究数据",
         goal="帮助医生理解真实世界证据的临床意义", difficulty="hard", category="product_intro",
         content="医生对RWS数据的质量有疑问，质疑其与RCT结果的一致性。你需要解释RWS的价值和局限性。",
         tips="诚实说明RWS与RCT的区别，强调互补关系而非替代关系。",
         scoring_weights=_S6, compliance_points=["RWS数据不可与RCT直接比较疗效", "需说明研究设计的局限性", "禁止选择性地报告有利数据"]),
    # 异议处理类（4种）
    dict(title="价格异议处理", role_setting="你是一名医药代表，医生认为你的产品价格过高",
         goal="合理回应价格疑虑，强调产品的 pharmacoeconomic 价值", difficulty="medium", category="objection",
         content="医生表示你的产品虽然疗效不错，但价格是竞品的两倍，在医保控费压力下难以选择使用。",
         tips="从 pharmacoeconomic 角度分析，强调长期治疗的成本效益，而非单纯价格对比。",
         scoring_weights=_S7, compliance_points=["禁止做出价格保证或承诺", "不得暗示回扣或利益", "需基于 pharmacoeconomic 数据"]),
    dict(title="疗效异议处理", role_setting="你是一名医药代表，医生对产品的疗效数据表示怀疑",
         goal="用循证医学证据消除医生的疗效疑虑", difficulty="hard", category="objection",
         content="医生阅读了一些质疑你产品疗效的最新文献，对你的产品疗效数据表示不信任。",
         tips="诚实面对文献争议点，提供更全面的证据链，不要回避负面信息。",
         scoring_weights=_S8, compliance_points=["禁止隐瞒负面研究结果", "需完整呈现证据全貌", "禁止选择性引用数据"]),
    dict(title="安全性异议处理", role_setting="你是一名医药代表，医生担心产品的不良反应问题",
         goal="客观说明安全性数据，建立医生对产品安全管理的信心", difficulty="medium", category="objection",
         content="医生在学术会议上听到关于你的产品可能引起严重不良反应的讨论，表达了对安全性的担忧。",
         tips="不要回避不良反应，提供 AE 数据、发生率和管理方案。",
         scoring_weights=_S9, compliance_points=["必须如实报告不良反应数据", "禁止淡化安全风险", "需提供 AE 管理建议"]),
    dict(title="竞品优势异议", role_setting="你是一名医药代表，医生认为竞品在某方面有明显优势",
         goal="合理应对竞品优势论述，维护产品定位", difficulty="hard", category="objection",
         content="医生列举了竞品在剂型便捷性、医保覆盖和患者依从性方面的优势，质疑你产品的临床实用性。",
         tips="承认竞品在某些维度的优势，转而强调本品在疗效深度和安全性方面的差异化价值。",
         scoring_weights=_S10, compliance_points=["禁止虚假贬低竞品", "需基于事实对比", "禁止误导医生"]),
    # 合规类（3种）
    dict(title="合规话术演练", role_setting="你是一名医药代表，模拟在合规框架下向医生进行产品介绍",
         goal="掌握合规推广的核心话术和红线标准", difficulty="easy", category="compliance",
         content="公司合规部门要求所有代表在限定范围内使用合规话术模板进行产品介绍练习。",
         tips="注意区分合规表述与非合规表述，熟悉公司 SOP 中的合规红线。",
         scoring_weights=_S11, compliance_points=["禁止使用绝对化用语", "禁止超出说明书范围", "禁止利益承诺"]),
    dict(title="利益冲突处理", role_setting="你是一名医药代表，医生暗示希望通过合作获取个人利益",
         goal="在保持良好关系的同时坚守合规底线", difficulty="hard", category="compliance",
         content="一位长期合作的老客户在交流中暗示，如果公司能提供一些'额外的支持'，他会增加处方量。",
         tips="坚守合规底线，礼貌拒绝不当要求，同时维系正常学术关系。",
         scoring_weights=_S12, compliance_points=["禁止利益输送", "禁止变相贿赂", "需符合公司合规政策和 anti-bribery 法规"]),
    dict(title="合规边界判断", role_setting="你是一名医药代表，需要判断各类场景是否触碰合规红线",
         goal="培养对复杂场景下合规边界的判断能力", difficulty="hard", category="compliance",
         content="面对一系列实际业务中遇到的边缘情况，判断哪些行为合规、哪些不合规并说明理由。",
         tips="对照行业规范和公司制度进行判断，不确定时以'宁紧勿松'为原则。",
         scoring_weights=_S13, compliance_points=["禁止灰色地带操作", "学术赞助须合规透明", "禁止现金或等价物往来"]),
    # 关单类（2种）
    dict(title="推进处方转化", role_setting="你是一名医药代表，经过多次拜访后希望推动医生开始处方",
         goal="在不施加不当压力的情况下促进处方转化", difficulty="medium", category="closing",
         content="经过三次拜访和学术交流，医生对产品表示了兴趣但尚未处方。你需要推动最后的转化。",
         tips="以临床需求为切入点，提供试用的学术支持，避免向医生施加压力。",
         scoring_weights=_S14, compliance_points=["禁止以利益诱导处方", "禁止用量承诺", "尊重医生独立处方权"]),
    dict(title="建立长期合作关系", role_setting="你是一名医药代表，希望与重点客户建立长期学术合作关系",
         goal="从单纯的交易关系升级为学术合作伙伴关系", difficulty="hard", category="closing",
         content="这位医生已经是产品的稳定使用者，你希望推进更深层次的学术合作，包括临床研究和学术会议支持。",
         tips="聚焦学术合作价值，提供临床研究参与机会和学术交流平台。",
         scoring_weights=_S15, compliance_points=["研究合作需符合 GCP 规范", "学术支持须透明合规", "禁止捆绑利益"]),
    # 竞品应对类（3种）
    dict(title="竞品负面信息应对", role_setting="你是一名医药代表，医生向你询问关于竞品的负面传闻",
         goal="在不诋毁竞品的前提下维护自身产品形象", difficulty="medium", category="competitor",
         content="医生提到在行业论坛上看到关于竞品安全性的负面讨论，想听听你的看法。",
         tips="不评论竞品具体事件，引导话题回归自身产品的循证优势。",
         scoring_weights=_S16, compliance_points=["禁止借机诋毁竞品", "禁止传播未经核实的信息", "客观陈述自身产品优势"]),
    dict(title="竞品学术活动分析", role_setting="你是一名医药代表，医生提到刚参加完竞品举办的学术会议",
         goal="了解竞品学术策略，寻找差异化机会", difficulty="medium", category="competitor",
         content="医生提到竞品举办的学术卫星会内容很精彩，展示了一些令人印象深刻的新数据。",
         tips="不要直接反驳医生对竞品的认可，而是通过自身学术优势建立差异化认知。",
         scoring_weights=_S17, compliance_points=["禁止贬低竞品学术内容", "客观评价自身学术资源", "以循证证据说话"]),
    dict(title="差异化定位策略", role_setting="你是一名医药代表，需要在同质化竞争中找到产品的独特卖点",
         goal="清晰阐述产品与竞品的本质差异，建立不可替代的定位", difficulty="hard", category="competitor",
         content="市场上有多个同类产品，医生认为'都差不多'。你需要展示你产品的独特临床价值。",
         tips="从机制、人群、剂型、证据等级等维度提炼差异化特点。",
         scoring_weights=_S18, compliance_points=["差异化表述须有据可查", "禁止无证据宣称 superior", "基于科学证据而非营销话术"]),
    # 科研沟通类（3种）
    dict(title="向PI介绍产品", role_setting="你是一名临床研究专员，向一位主要研究者（PI）介绍产品的临床研究计划",
         goal="获得PI对开展临床研究的兴趣和支持", difficulty="hard", category="research",
         content="你向一位知名PI介绍一项即将开展的多中心临床研究方案，希望他/她作为牵头研究者参与。",
         tips="以科学价值为切入点，强调研究设计的严谨性和对学术领域的贡献。",
         scoring_weights=_S19, compliance_points=["研究方案需经伦理审批", "禁止选择性报告结果", "遵循 GCP 和 ICH 指南"]),
    dict(title="科研合作方案探讨", role_setting="你是一名医学科学联络官（MSL），与医生探讨科研合作的可能性",
         goal="推动与学术机构的科研合作项目", difficulty="hard", category="research",
         content="一位学术声望很高的教授对你的领域感兴趣，希望探讨合作开展一项研究者发起的研究（IIT）的可能性。",
         tips="明确公司对IIT的支持政策和审批流程，确保合作合规透明。",
         scoring_weights=_S20, compliance_points=["IIT须签订正式协议", "资助须公开透明", "研究结果发表须遵守 ICMJE 规则"]),
    dict(title="学术会议交流", role_setting="你是一名医学事务人员，参加国际学术会议期间与专家进行学术交流",
         goal="在会议场景下高效传递学术信息，拓展学术网络", difficulty="medium", category="research",
         content="在学术会议的展台和社交环节，多位专家对你的产品最新研究数据表现出兴趣。",
         tips="准备简洁的核心信息，注意会议场合的合规要求，不要过度宣传。",
         scoring_weights=_S21, compliance_points=["会议推广须遵守举办国法规", "禁止在展台外推广", "学术材料须合规审批"]),
]


def get_scenarios_by_category(category: str) -> List[dict]:
    """Return all fixed scenarios matching the given category."""
    return [s for s in FIXED_SCENARIOS if s["category"] == category]


def get_scenario_by_difficulty(difficulty: str) -> List[dict]:
    """Return all fixed scenarios matching the given difficulty level."""
    return [s for s in FIXED_SCENARIOS if s["difficulty"] == difficulty]


def generate_training_scenarios() -> List[dict]:
    entities = _read_kg_entities(["drug", "disease"])
    if not entities:
        return []

    now = datetime.now(timezone.utc).isoformat()
    scenarios = []
    templates = []

    for e in entities:
        etype = e["entity_type"]
        name = e["name"]
        props = {}
        try:
            props = json.loads(e["properties"] or "{}")
        except (json.JSONDecodeError, TypeError):
            pass

        if etype == "drug":
            category = props.get("category", "药品知识")
            templates.append({
                "title": f"产品知识：{name}的临床应用",
                "role_setting": f"你是一名医药代表，正在向医生介绍{name}",
                "goal": f"让医生充分了解{name}的临床价值和适用范围",
                "difficulty": "medium", "category": "drug",
                "content": f"请详细介绍{name}（{category}）的核心临床数据、适用患者人群及安全性信息。",
                "tips": f"重点突出{name}的差异化优势，避免绝对化表述。",
            })
        elif etype == "disease":
            prevalence = props.get("prevalence", "")
            desc_suffix = f"（{prevalence}流行病学数据）" if prevalence else ""
            templates.append({
                "title": f"疾病教育：{name}的诊疗沟通",
                "role_setting": f"你是一名医学信息顾问，需要向医生提供{name}的学术支持",
                "goal": f"通过提供{name}的权威诊疗信息建立学术信任",
                "difficulty": "medium", "category": "disease",
                "content": f"请向医生介绍{name}{desc_suffix}的最新诊疗指南和临床研究进展。",
                "tips": f"使用循证医学证据，引用权威指南，展示专业价值。",
            })

    templates = templates[:5]
    for t in templates:
        t["created_at"] = now
        t["updated_at"] = now
        t["is_active"] = 1
        scenarios.append(t)

    return scenarios


def append_scenarios_to_db(conn: sqlite3.Connection, scenarios: List[dict], created_by: int = 1) -> int:
    count = 0
    for sc in scenarios:
        conn.execute(
            "INSERT INTO coach_scenario (title, role_setting, goal, difficulty, "
            "category, content, tips, is_active, created_by, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (sc["title"], sc["role_setting"], sc["goal"], sc["difficulty"], sc["category"],
             sc["content"], sc["tips"], sc["is_active"], created_by, sc["created_at"], sc["updated_at"]),
        )
        count += 1
    conn.commit()
    return count
