"""患者游戏化激励服务。"""

from datetime import date, timedelta
from typing import Any
from uuid import uuid4

from shared.datetime_utils import utc_now

from ..schemas.gamification import PatientPoints, PointsBreakdown, RedemptionRecord, RewardOption

_PATIENT_POINTS: dict[str, PatientPoints] = {}
_REDEMPTIONS: list[RedemptionRecord] = []

_REWARDS = [
    RewardOption(
        id="reward-health-kit",
        name="健康管理礼包",
        description="血压记录本、药盒与健康教育材料",
        points_required=100,
    ),
    RewardOption(
        id="reward-consultation",
        name="线上健康咨询",
        description="兑换一次慢病管理线上咨询服务",
        points_required=200,
    ),
    RewardOption(
        id="reward-priority-followup",
        name="优先随访名额",
        description="优先安排一次护理随访",
        points_required=300,
    ),
]


def _get_or_create_points(patient_id: str) -> PatientPoints:
    """获取或创建患者积分记录。

    Args:
        patient_id: 患者唯一标识

    Returns:
        该患者的积分对象
    """
    if patient_id not in _PATIENT_POINTS:
        _PATIENT_POINTS[patient_id] = PatientPoints(patient_id=patient_id)
    return _PATIENT_POINTS[patient_id]


def _level_for_points(total_points: int) -> str:
    """根据总积分计算等级。

    Args:
        total_points: 总积分值

    Returns:
        等级名称（Bronze/Silver/Gold/Platinum）
    """
    if total_points >= 500:
        return "Platinum"
    if total_points >= 300:
        return "Gold"
    if total_points >= 150:
        return "Silver"
    return "Bronze"


def _checkin_dates(points: PatientPoints) -> set[date]:
    """提取积分记录中的签到日期集合。

    Args:
        points: 患者积分对象

    Returns:
        签到日期集合
    """
    return {item.date.date() for item in points.points_breakdown if item.action in {"checkin", "daily_checkin"}}


def _calculate_streak(points: PatientPoints, include_today: bool = True) -> int:
    """计算连续签到天数。

    Args:
        points: 患者积分对象
        include_today: 是否包含今天

    Returns:
        连续签到天数
    """
    dates = _checkin_dates(points)
    current = utc_now().date() if include_today else utc_now().date() - timedelta(days=1)
    streak = 0
    while current in dates:
        streak += 1
        current -= timedelta(days=1)
    return streak


async def award_points(patient_id: str, action: str) -> dict[str, Any]:
    """发放积分，签到每天 +10，连续 7 天额外 +50。

    Args:
        patient_id: 患者唯一标识
        action: 操作类型（checkin/daily_checkin/签到或其他）

    Returns:
        包含 earned_points、awarded_actions、total_points、level、streak_days 的字典
    """
    points = _get_or_create_points(patient_id)
    today = utc_now().date()
    normalized_action = "checkin" if action in {"checkin", "daily_checkin", "签到"} else action

    earned = 0
    awarded_actions: list[dict[str, Any]] = []
    existing_dates = _checkin_dates(points)
    if normalized_action == "checkin":
        if today not in existing_dates:
            earned += 10
            points.points_breakdown.append(PointsBreakdown(action="checkin", points=10, date=utc_now()))
            awarded_actions.append({"action": "checkin", "points": 10})

            points.streak_days = _calculate_streak(points)
            if points.streak_days and points.streak_days % 7 == 0:
                earned += 50
                points.points_breakdown.append(PointsBreakdown(action="streak_7_days_bonus", points=50, date=utc_now()))
                awarded_actions.append({"action": "streak_7_days_bonus", "points": 50})
        else:
            points.streak_days = _calculate_streak(points)
    else:
        action_points = 5
        earned += action_points
        points.points_breakdown.append(PointsBreakdown(action=normalized_action, points=action_points, date=utc_now()))
        awarded_actions.append({"action": normalized_action, "points": action_points})
        points.streak_days = _calculate_streak(points)

    points.total_points += earned
    points.level = _level_for_points(points.total_points)

    return {
        "patient_id": patient_id,
        "earned_points": earned,
        "awarded_actions": awarded_actions,
        "total_points": points.total_points,
        "level": points.level,
        "streak_days": points.streak_days,
    }


async def get_points(patient_id: str) -> dict[str, Any]:
    """查询患者积分账户信息。

    Args:
        patient_id: 患者唯一标识

    Returns:
        患者积分账户的完整信息（JSON格式）
    """
    points = _get_or_create_points(patient_id)
    points.streak_days = _calculate_streak(points)
    points.level = _level_for_points(points.total_points)
    return points.model_dump(mode="json")


async def get_rewards() -> list[dict[str, Any]]:
    """查询可兑换的奖励列表。

    Returns:
        可兑换奖励列表（JSON格式）
    """
    return [reward.model_dump(mode="json") for reward in _REWARDS]


async def get_leaderboard() -> dict[str, Any]:
    """查询积分排行榜（前20名）。

    Returns:
        包含 leaderboard 列表和 generated_at 的字典
    """
    rows = sorted(_PATIENT_POINTS.values(), key=lambda item: item.total_points, reverse=True)
    return {
        "leaderboard": [
            {
                "rank": index + 1,
                "patient_id": item.patient_id,
                "total_points": item.total_points,
                "level": item.level,
                "streak_days": item.streak_days,
            }
            for index, item in enumerate(rows[:20])
        ],
        "generated_at": utc_now().isoformat(),
    }


async def redeem_reward(patient_id: str, reward_id: str) -> dict[str, Any]:
    """兑换奖励。

    Args:
        patient_id: 患者唯一标识
        reward_id: 奖励唯一标识

    Returns:
        成功时包含兑换记录和剩余积分，失败时包含失败原因
    """
    points = _get_or_create_points(patient_id)
    reward = next((item for item in _REWARDS if item.id == reward_id), None)
    if reward is None:
        return {
            "patient_id": patient_id,
            "reward_id": reward_id,
            "status": "failed",
            "reason": "reward_not_found",
        }

    if points.total_points < reward.points_required:
        return {
            "patient_id": patient_id,
            "reward_id": reward_id,
            "status": "failed",
            "reason": "insufficient_points",
            "points_required": reward.points_required,
            "current_points": points.total_points,
        }

    points.total_points -= reward.points_required
    points.level = _level_for_points(points.total_points)
    record = RedemptionRecord(
        id=f"RDM-{uuid4().hex[:10]}",
        patient_id=patient_id,
        reward_id=reward_id,
        points_spent=reward.points_required,
        redeemed_at=utc_now(),
    )
    _REDEMPTIONS.append(record)
    return {
        "redemption": record.model_dump(mode="json"),
        "remaining_points": points.total_points,
        "level": points.level,
    }
