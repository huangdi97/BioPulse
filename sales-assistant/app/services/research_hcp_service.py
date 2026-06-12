"""Research HCP enrichment service."""

from sales_assistant.app.schemas.research_hcp import (
    ExperimentMethod,
    GrantInfo,
    PaperInfo,
    ResearchProfile,
)

_PAPERS: dict[str, list[PaperInfo]] = {
    "hcp-001": [
        PaperInfo(
            id="paper-001",
            title="Immunotherapy biomarkers in advanced NSCLC",
            journal="Journal of Thoracic Oncology",
            year=2024,
            citations=42,
            impact_factor=20.4,
        ),
        PaperInfo(
            id="paper-002",
            title="Real-world outcomes of combination therapy",
            journal="Clinical Cancer Research",
            year=2025,
            citations=28,
            impact_factor=13.8,
        ),
        PaperInfo(
            id="paper-003",
            title="ctDNA monitoring for treatment response",
            journal="Lung Cancer",
            year=2023,
            citations=16,
            impact_factor=6.1,
        ),
    ]
}

_GRANTS: dict[str, list[GrantInfo]] = {
    "hcp-001": [
        GrantInfo(
            id="grant-001",
            title="肺癌免疫治疗耐药机制研究",
            source="国家自然科学基金",
            amount=580000,
            year=2025,
            status="active",
        ),
        GrantInfo(
            id="grant-002",
            title="真实世界队列与生物标志物转化研究",
            source="省部级重点项目",
            amount=350000,
            year=2024,
            status="active",
        ),
    ]
}

_EXPERIMENTS: dict[str, list[ExperimentMethod]] = {
    "hcp-001": [
        ExperimentMethod(
            id="exp-001",
            name="ctDNA NGS",
            category="molecular",
            description="用于疗效监测和耐药突变识别。",
        ),
        ExperimentMethod(
            id="exp-002",
            name="多重免疫组化",
            category="pathology",
            description="评估肿瘤微环境免疫细胞浸润。",
        ),
    ]
}


def _fallback_papers(hcp_id: str) -> list[PaperInfo]:
    """生成默认论文列表（当指定 HCP 无论文数据时使用）。

    Args:
        hcp_id: HCP 唯一标识符。

    Returns:
        包含一条默认论文信息的列表。
    """
    return [
        PaperInfo(
            id=f"paper-{hcp_id}-001",
            title="Clinical research profile pending curation",
            journal="Internal Research Index",
            year=2026,
            citations=6,
            impact_factor=3.2,
        )
    ]


def get_papers(hcp_id: str) -> list[PaperInfo]:
    """获取指定 HCP 的论文列表。

    Args:
        hcp_id: HCP 唯一标识符。

    Returns:
        论文信息列表，若无数据则返回默认值。
    """
    return _PAPERS.get(hcp_id, _fallback_papers(hcp_id))


def get_grants(hcp_id: str) -> list[GrantInfo]:
    """获取指定 HCP 的科研基金信息。

    Args:
        hcp_id: HCP 唯一标识符。

    Returns:
        基金信息列表，若无数据则返回默认值。
    """
    return _GRANTS.get(
        hcp_id,
        [
            GrantInfo(
                id=f"grant-{hcp_id}-001",
                title="科研合作潜力项目",
                source="院内课题",
                amount=80000,
                year=2026,
                status="planned",
            )
        ],
    )


def calc_h_index(papers: list[PaperInfo]) -> int:
    """计算 H 指数。

    Args:
        papers: 论文信息列表。

    Returns:
        计算所得的 H 指数值。
    """
    citations = sorted((paper.citations for paper in papers), reverse=True)
    h_index = 0
    for idx, citation_count in enumerate(citations, start=1):
        if citation_count >= idx:
            h_index = idx
        else:
            break
    return h_index


def extract_experiment_methods(hcp_id: str) -> list[ExperimentMethod]:
    """获取指定 HCP 的实验方法列表。

    Args:
        hcp_id: HCP 唯一标识符。

    Returns:
        实验方法信息列表，若无数据则返回默认值。
    """
    return _EXPERIMENTS.get(
        hcp_id,
        [
            ExperimentMethod(
                id=f"exp-{hcp_id}-001",
                name="临床队列分析",
                category="clinical",
                description="从病例队列中提取疗效与安全性信号。",
            )
        ],
    )


def get_comprehensive_score(profile: ResearchProfile) -> float:
    """计算 HCP 研究综合评分。

    Args:
        profile: HCP 研究画像对象。

    Returns:
        综合评分值（满分 100）。
    """
    paper_score = min(len(profile.papers) * 12, 36)
    grant_score = min(len(profile.grants) * 14, 28)
    h_index_score = min(profile.h_index * 4, 24)
    method_score = min(len(profile.experiments) * 4, 12)
    return round(paper_score + grant_score + h_index_score + method_score, 2)


def enrich_research_profile(hcp_id: str) -> ResearchProfile:
    """丰富 HCP 研究画像数据。

    综合获取论文、基金、实验方法等信息，并计算 H 指数、影响因子和综合评分。

    Args:
        hcp_id: HCP 唯一标识符。

    Returns:
        包含完整研究画像数据的 ResearchProfile 对象。
    """
    papers = get_papers(hcp_id)
    grants = get_grants(hcp_id)
    experiments = extract_experiment_methods(hcp_id)
    h_index = calc_h_index(papers)
    impact_factor = round(sum(paper.impact_factor for paper in papers), 2)
    profile = ResearchProfile(
        papers=papers,
        grants=grants,
        experiments=experiments,
        h_index=h_index,
        impact_factor=impact_factor,
        score=0,
    )
    return profile.model_copy(update={"score": get_comprehensive_score(profile)})
