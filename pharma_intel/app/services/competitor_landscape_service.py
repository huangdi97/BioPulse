"""竞争格局视图服务。"""

from typing import Optional

from pharma_intel.app.schemas.competitor_landscape import (
    LandscapeComparison,
    LandscapeCompetitor,
    LandscapeDimension,
    RadarData,
    RadarSeries,
)

COMPETITORS = [
    LandscapeCompetitor(
        id="cmp-merck",
        name="Merck",
        therapy_area="tumor",
        dimension_scores={
            LandscapeDimension.PIPELINE_PROGRESS: 94,
            LandscapeDimension.TARGET_COVERAGE: 86,
            LandscapeDimension.INDICATION_COVERAGE: 92,
            LandscapeDimension.CLINICAL_STAGE: 96,
        },
    ),
    LandscapeCompetitor(
        id="cmp-astrazeneca",
        name="AstraZeneca",
        therapy_area="tumor",
        dimension_scores={
            LandscapeDimension.PIPELINE_PROGRESS: 90,
            LandscapeDimension.TARGET_COVERAGE: 88,
            LandscapeDimension.INDICATION_COVERAGE: 84,
            LandscapeDimension.CLINICAL_STAGE: 91,
        },
    ),
    LandscapeCompetitor(
        id="cmp-jj",
        name="Johnson & Johnson",
        therapy_area="tumor",
        dimension_scores={
            LandscapeDimension.PIPELINE_PROGRESS: 82,
            LandscapeDimension.TARGET_COVERAGE: 80,
            LandscapeDimension.INDICATION_COVERAGE: 78,
            LandscapeDimension.CLINICAL_STAGE: 86,
        },
    ),
    LandscapeCompetitor(
        id="cmp-beigene",
        name="BeiGene",
        therapy_area="hematology",
        dimension_scores={
            LandscapeDimension.PIPELINE_PROGRESS: 84,
            LandscapeDimension.TARGET_COVERAGE: 76,
            LandscapeDimension.INDICATION_COVERAGE: 80,
            LandscapeDimension.CLINICAL_STAGE: 88,
        },
    ),
]

TARGET_COMPETITOR_MAP = {
    "tgt-pd1": ["cmp-merck", "cmp-beigene"],
    "tgt-egfr": ["cmp-astrazeneca", "cmp-jj"],
    "tgt-cldn18-2": ["cmp-astrazeneca"],
    "tgt-btk": ["cmp-beigene", "cmp-jj"],
}


def get_landscape_matrix(
    therapy_area: Optional[str] = None,
    competitor_ids: Optional[list[str]] = None,
) -> LandscapeComparison:
    competitors = COMPETITORS
    if therapy_area:
        needle = therapy_area.lower()
        competitors = [item for item in competitors if item.therapy_area.lower() == needle]
    if competitor_ids:
        selected = set(competitor_ids)
        competitors = [item for item in competitors if item.id in selected]
    return LandscapeComparison(competitors=competitors)


def get_radar_chart_data(target_id: str) -> RadarData:
    competitor_ids = TARGET_COMPETITOR_MAP.get(target_id, [])
    comparison = get_landscape_matrix(competitor_ids=competitor_ids)
    dimensions = list(LandscapeDimension)
    series = [
        RadarSeries(
            competitor_id=competitor.id,
            competitor_name=competitor.name,
            scores=competitor.dimension_scores,
        )
        for competitor in comparison.competitors
    ]
    return RadarData(target_id=target_id, dimensions=dimensions, series=series)
