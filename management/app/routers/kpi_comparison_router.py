"""团队 KPI 对比看板 API。"""

from fastapi import APIRouter, Query

from management.app.services.kpi_comparison_service import (
    KPIDimension,
    KPIPeriod,
    get_kpi_history,
    get_team_ranking,
)
from shared.base import success

router = APIRouter(prefix="/api/kpi", tags=["团队KPI"])


@router.get("/ranking", summary="团队 KPI 排名", description="按合规、拜访或任务完成维度获取团队 KPI 排名", tags=["团队KPI"])
def team_ranking(
    dimension: KPIDimension = Query("compliance", description="排名维度: compliance/visit/task"),
    period: KPIPeriod = Query("weekly", description="统计周期: weekly/monthly/quarterly"),
):
    data = get_team_ranking(dimension=dimension, period=period)
    return success(data=data)


@router.get("/team/{team_id}", summary="团队 KPI 历史", description="获取单个团队的 KPI 周/月/季度历史", tags=["团队KPI"])
def team_kpi_history(
    team_id: str,
    period: KPIPeriod = Query("monthly", description="统计周期: weekly/monthly/quarterly"),
):
    data = get_kpi_history(team_id=team_id, period=period)
    return success(data=data)
