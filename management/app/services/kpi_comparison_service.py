"""团队 KPI 对比看板服务。"""

from typing import Literal

from fastapi import HTTPException
from starlette import status

from management.app.schemas.kpi_comparison import KPIHistoryPoint, TeamKPI

KPIDimension = Literal["compliance", "visit", "task"]
KPIPeriod = Literal["weekly", "monthly", "quarterly"]

DIMENSION_FIELD = {
    "compliance": "compliance_rate",
    "visit": "visit_completion_rate",
    "task": "task_completion_rate",
}

PERIOD_LABELS = {
    "weekly": ["W-5", "W-4", "W-3", "W-2", "W-1", "W"],
    "monthly": ["M-5", "M-4", "M-3", "M-2", "M-1", "M"],
    "quarterly": ["Q-5", "Q-4", "Q-3", "Q-2", "Q-1", "Q"],
}

BASE_TEAM_DATA = [
    {
        "team_id": "team-east",
        "team_name": "华东团队",
        "compliance_rate": 96.4,
        "visit_completion_rate": 92.1,
        "task_completion_rate": 94.8,
        "avg_engagement_score": 88.6,
    },
    {
        "team_id": "team-south",
        "team_name": "华南团队",
        "compliance_rate": 93.8,
        "visit_completion_rate": 95.3,
        "task_completion_rate": 91.7,
        "avg_engagement_score": 86.9,
    },
    {
        "team_id": "team-north",
        "team_name": "华北团队",
        "compliance_rate": 91.6,
        "visit_completion_rate": 89.7,
        "task_completion_rate": 93.2,
        "avg_engagement_score": 84.1,
    },
    {
        "team_id": "team-west",
        "team_name": "西区团队",
        "compliance_rate": 89.9,
        "visit_completion_rate": 87.6,
        "task_completion_rate": 88.5,
        "avg_engagement_score": 81.4,
    },
]

PERIOD_ADJUSTMENTS = {
    "weekly": 0.0,
    "monthly": 1.2,
    "quarterly": 2.0,
}


def _clamp_pct(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 1)


def _periodized_teams(period: KPIPeriod) -> list[dict]:
    adjustment = PERIOD_ADJUSTMENTS[period]
    teams = []
    for index, item in enumerate(BASE_TEAM_DATA):
        drift = adjustment - index * 0.4
        teams.append(
            {
                **item,
                "compliance_rate": _clamp_pct(item["compliance_rate"] + drift),
                "visit_completion_rate": _clamp_pct(item["visit_completion_rate"] + drift * 0.8),
                "task_completion_rate": _clamp_pct(item["task_completion_rate"] + drift * 0.7),
                "avg_engagement_score": _clamp_pct(item["avg_engagement_score"] + drift * 0.5),
            }
        )
    return teams


def get_team_ranking(dimension: KPIDimension, period: KPIPeriod) -> list[TeamKPI]:
    """按指定 KPI 维度返回团队排名。"""

    rank_field = DIMENSION_FIELD[dimension]
    ranked = sorted(_periodized_teams(period), key=lambda item: item[rank_field], reverse=True)
    return [TeamKPI(**team, rank=rank) for rank, team in enumerate(ranked, start=1)]


def get_kpi_history(team_id: str, period: KPIPeriod) -> dict:
    """返回单个团队的周/月/季度 KPI 历史。"""

    teams = _periodized_teams(period)
    team = next((item for item in teams if item["team_id"] == team_id), None)
    if team is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Team not found")

    points = []
    labels = PERIOD_LABELS[period]
    for offset, label in enumerate(labels):
        delta = (offset - len(labels) + 1) * 0.9
        points.append(
            KPIHistoryPoint(
                period_label=label,
                compliance_rate=_clamp_pct(team["compliance_rate"] + delta),
                visit_completion_rate=_clamp_pct(team["visit_completion_rate"] + delta * 0.8),
                task_completion_rate=_clamp_pct(team["task_completion_rate"] + delta * 0.7),
                avg_engagement_score=_clamp_pct(team["avg_engagement_score"] + delta * 0.5),
            )
        )

    return {
        "team_id": team["team_id"],
        "team_name": team["team_name"],
        "period": period,
        "history": points,
    }
