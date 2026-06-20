"""场景加载器，从固定场景模板加载场景数据。"""

from typing import List

from .scenario_template import FIXED_SCENARIOS_PART1
from .scenario_weights import _S14, _S15, _S16, _S17, _S18, _S19, _S20, _S21


class ScenarioLoader:
    def get_scenarios_by_category(self, category: str) -> List[dict]:
        return [s for s in FIXED_SCENARIOS if s["category"] == category]

    def get_scenario_by_difficulty(self, difficulty: str) -> List[dict]:
        return [s for s in FIXED_SCENARIOS if s["difficulty"] == difficulty]


FIXED_SCENARIOS_PART2 = [
    dict(
        title="推进处方转化",
        role_setting="你是一名医药代表，经过多次拜访后希望推动医生开始处方",
        goal="在不施加不当压力的情况下促进处方转化",
        difficulty="medium",
        category="closing",
        content="经过三次拜访和学术交流，医生对产品表示了兴趣但尚未处方。你需要推动最后的转化。",
        tips="以临床需求为切入点，提供试用的学术支持，避免向医生施加压力。",
        scoring_weights=_S14,
        compliance_points=["禁止以利益诱导处方", "禁止用量承诺", "尊重医生独立处方权"],
    ),
    dict(
        title="建立长期合作关系",
        role_setting="你是一名医药代表，希望与重点客户建立长期学术合作关系",
        goal="从单纯的交易关系升级为学术合作伙伴关系",
        difficulty="hard",
        category="closing",
        content="这位医生已经是产品的稳定使用者，你希望推进更深层次的学术合作，包括临床研究和学术会议支持。",
        tips="聚焦学术合作价值，提供临床研究参与机会和学术交流平台。",
        scoring_weights=_S15,
        compliance_points=["研究合作需符合 GCP 规范", "学术支持须透明合规", "禁止捆绑利益"],
    ),
    dict(
        title="竞品负面信息应对",
        role_setting="你是一名医药代表，医生向你询问关于竞品的负面传闻",
        goal="在不诋毁竞品的前提下维护自身产品形象",
        difficulty="medium",
        category="competitor",
        content="医生提到在行业论坛上看到关于竞品安全性的负面讨论，想听听你的看法。",
        tips="不评论竞品具体事件，引导话题回归自身产品的循证优势。",
        scoring_weights=_S16,
        compliance_points=["禁止借机诋毁竞品", "禁止传播未经核实的信息", "客观陈述自身产品优势"],
    ),
    dict(
        title="竞品学术活动分析",
        role_setting="你是一名医药代表，医生提到刚参加完竞品举办的学术会议",
        goal="了解竞品学术策略，寻找差异化机会",
        difficulty="medium",
        category="competitor",
        content="医生提到竞品举办的学术卫星会内容很精彩，展示了一些令人印象深刻的新数据。",
        tips="不要直接反驳医生对竞品的认可，而是通过自身学术优势建立差异化认知。",
        scoring_weights=_S17,
        compliance_points=["禁止贬低竞品学术内容", "客观评价自身学术资源", "以循证证据说话"],
    ),
    dict(
        title="差异化定位策略",
        role_setting="你是一名医药代表，需要在同质化竞争中找到产品的独特卖点",
        goal="清晰阐述产品与竞品的本质差异，建立不可替代的定位",
        difficulty="hard",
        category="competitor",
        content="市场上有多个同类产品，医生认为'都差不多'。你需要展示你产品的独特临床价值。",
        tips="从机制、人群、剂型、证据等级等维度提炼差异化特点。",
        scoring_weights=_S18,
        compliance_points=[
            "差异化表述须有据可查",
            "禁止无证据宣称 superior",
            "基于科学证据而非营销话术",
        ],
    ),
    dict(
        title="向PI介绍产品",
        role_setting="你是一名临床研究专员，向一位主要研究者（PI）介绍产品的临床研究计划",
        goal="获得PI对开展临床研究的兴趣和支持",
        difficulty="hard",
        category="research",
        content="你向一位知名PI介绍一项即将开展的多中心临床研究方案，希望他/她作为牵头研究者参与。",
        tips="以科学价值为切入点，强调研究设计的严谨性和对学术领域的贡献。",
        scoring_weights=_S19,
        compliance_points=["研究方案需经伦理审批", "禁止选择性报告结果", "遵循 GCP 和 ICH 指南"],
    ),
    dict(
        title="科研合作方案探讨",
        role_setting="你是一名医学科学联络官（MSL），与医生探讨科研合作的可能性",
        goal="推动与学术机构的科研合作项目",
        difficulty="hard",
        category="research",
        content="一位学术声望很高的教授对你的领域感兴趣，希望探讨合作开展一项研究者发起的研究（IIT）的可能性。",
        tips="明确公司对IIT的支持政策和审批流程，确保合作合规透明。",
        scoring_weights=_S20,
        compliance_points=["IIT须签订正式协议", "资助须公开透明", "研究结果发表须遵守 ICMJE 规则"],
    ),
    dict(
        title="学术会议交流",
        role_setting="你是一名医学事务人员，参加国际学术会议期间与专家进行学术交流",
        goal="在会议场景下高效传递学术信息，拓展学术网络",
        difficulty="medium",
        category="research",
        content="在学术会议的展台和社交环节，多位专家对你的产品最新研究数据表现出兴趣。",
        tips="准备简洁的核心信息，注意会议场合的合规要求，不要过度宣传。",
        scoring_weights=_S21,
        compliance_points=[
            "会议推广须遵守举办国法规",
            "禁止在展台外推广",
            "学术材料须合规审批",
        ],
    ),
]

FIXED_SCENARIOS = FIXED_SCENARIOS_PART1 + FIXED_SCENARIOS_PART2
