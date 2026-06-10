"""统计路由模块，提供教练数据的聚合统计、趋势、团队对比及雷达图接口。"""

from typing import List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from sales_coach.app.services.stats_service import StatsService
from shared.auth_scope import require_scope
from shared.base import ApiResponse, success

router = APIRouter(prefix="/coach")


class ModuleDistItem(BaseModel):
    module_id: int
    module_title: str
    count: int
    avg_score: float


class TopTraineeItem(BaseModel):
    trainee_name: str
    avg_score: float
    session_count: int


class StatsOut(BaseModel):
    total_assessments: int
    average_score: float
    module_distribution: List[ModuleDistItem]
    top_trainees: List[TopTraineeItem]
    score_distribution: dict


@router.get("/stats", summary="教练统计", description="教练模块的聚合统计数据", tags=["评估"])
def get_stats(
    service: StatsService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse[StatsOut]:
    """Aggregate coaching stats from coach_session."""
    data = service.get_stats()
    return success(
        data=StatsOut(
            total_assessments=data["total_assessments"],
            average_score=data["average_score"],
            module_distribution=[
                ModuleDistItem(
                    module_id=m["module_id"],
                    module_title=m["module_title"],
                    count=m["count"],
                    avg_score=m["avg_score"],
                )
                for m in data["module_distribution"]
            ],
            top_trainees=[
                TopTraineeItem(
                    trainee_name=t["trainee_name"],
                    avg_score=t["avg_score"],
                    session_count=t["session_count"],
                )
                for t in data["top_trainees"]
            ],
            score_distribution=data["score_distribution"],
        )
    )


@router.get("/trend/{user_id}", summary="个人趋势", description="获取个人评分月度趋势数据", tags=["评估"])
def get_user_trend(
    user_id: int,
    months: int = Query(6, ge=1, le=24),
    service: StatsService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """获取个人评分趋势（月度聚合）。"""
    trend = service.get_user_trend(user_id, months=months)
    return success(data={"user_id": user_id, "trend": trend})


@router.get("/team-comparison/{team_id}", summary="团队对比", description="获取指定团队的评分对比数据", tags=["评估"])
def get_team_comparison(
    team_id: int,
    service: StatsService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """获取团队对比数据。"""
    data = service.get_team_comparison(team_id)
    return success(data={"team_id": team_id, **data})


@router.get("/radar/{user_id}", summary="雷达图", description="获取各维度评分的雷达图数据", tags=["评估"])
def get_radar(
    user_id: int,
    service: StatsService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """获取雷达图数据（各维度平均分）。"""
    data = service.get_radar_data(user_id)
    return success(data={"user_id": user_id, "dimensions": data})


@router.get("/category-performance/{user_id}", summary="分类表现", description="获取各类场景下的表现对比数据", tags=["评估"])
def get_category_performance(
    user_id: int,
    service: StatsService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """获取各类场景的表现对比。"""
    data = service.get_category_performance(user_id)
    return success(data={"user_id": user_id, "categories": data})


stats_root_router = APIRouter(tags=["stats"])


@stats_root_router.get("/stats", summary="根统计", description="前端兼容的根路径统计接口")
def get_stats_root(
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """GET /stats endpoint for frontend compatibility."""
    return success(data={})
