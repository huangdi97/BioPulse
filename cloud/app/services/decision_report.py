"""决策报表模块，提供仪表盘等汇总报表功能。"""

from cloud.app.repositories import (
    CausalAnalysesRepository,
    CrossCaseInsightsRepository,
    DecisionCasesRepository,
)


class DecisionReportMixin:
    """决策报表混入类，提供汇总统计与仪表盘功能。"""

    def dashboard(self) -> dict:
        case_repo = DecisionCasesRepository(self._connection())
        analysis_repo = CausalAnalysesRepository(self._connection())
        insight_repo = CrossCaseInsightsRepository(self._connection())
        total_cases = case_repo.count_active()
        analyzed = analysis_repo.count_distinct_case_ids()
        score_dist = case_repo.score_distribution()
        insight_counts = insight_repo.count_by_type()
        top_insights = insight_repo.top_by_confidence(5)
        return {
            "total_cases": total_cases,
            "analyzed_cases": analyzed,
            "score_distribution": score_dist,
            "insights_by_type": insight_counts,
            "top_insights": top_insights,
        }
