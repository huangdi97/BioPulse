"""患者游戏化激励路由。"""

from fastapi import APIRouter, Depends

from shared.auth_scope import require_scope
from shared.base import success

from ..schemas.gamification import RedeemRequest
from ..services.gamification_service import (
    get_leaderboard,
    get_points,
    get_rewards,
    redeem_reward,
)

router = APIRouter(prefix="/api/gamification")


@router.get("/points/{patient_id}", tags=["游戏化激励"])
async def points(patient_id: str):
    """查询患者积分。"""
    result = await get_points(patient_id)
    return success(data=result)


@router.post("/redeem", tags=["游戏化激励"])
async def redeem(body: RedeemRequest, _: dict = Depends(require_scope("visit"))):
    """兑换奖励。"""
    result = await redeem_reward(body.patient_id, body.reward_id)
    return success(data=result)


@router.get("/rewards", tags=["游戏化激励"])
async def rewards():
    """查询可兑换奖励。"""
    result = await get_rewards()
    return success(data=result)


@router.get("/leaderboard", tags=["游戏化激励"])
async def leaderboard():
    """查询积分排行榜。"""
    result = await get_leaderboard()
    return success(data=result)
